#include "hal_data.h"
#include <bsp_elc.h>
void R_BSP_WarmStart(bsp_warm_start_event_t event);

/* Change pins as needed here */
#define ICU_CHANNEL 0  // freely choosable from 0 to 15
#define NVIC_ICU_IRQ 0 // freely choosable position in the vector table (0 to 31)
#if defined(ARDUINO_UNOR4_WIFI)
#define LED         BSP_IO_PORT_01_PIN_02 // Yellow
#define BUTTON      BSP_IO_PORT_01_PIN_04 // "D2"
// must match "Renesas RA4M1 Group - User's Manual: Hardware"
// "Register settings for input/output pin function", "ISEL bit"
// NOT ALL PINS ARE INTERRUPT CAPABLE!!
// P105 has "IRQ1"
#define ELC_EVENT_TO_LINK ELC_EVENT_ICU_IRQ1  /* ICU IRQ1 (External pin interrupt 1) */
#elif defined(ARDUINO_UNOR4_MINIMA)
#define LED    BSP_IO_PORT_01_PIN_11 // Yellow
#define BUTTON BSP_IO_PORT_01_PIN_05 // "D2"
// P105 has "IRQ0"
#define ELC_EVENT_TO_LINK ELC_EVENT_ICU_IRQ0  /* ICU IRQ0 (External pin interrupt 0) */
#elif defined(ARDUINO_PORTENTA_C33)
#define LED    BSP_IO_PORT_01_PIN_07 // Red
#define BUTTON BSP_IO_PORT_01_PIN_11 // "D2"
// P111 has "IRQ4"
#define ELC_EVENT_TO_LINK ELC_EVENT_ICU_IRQ4  /* ICU IRQ4 (External pin interrupt 4) */
#else
#error "Unknown board, please set LED and Button pin"
#endif

// linker script and CMSIS symbols
extern const uint32_t __StackTop;
const uint32_t *APPLICATION_VECTOR_TABLE_ADDRESS_RAM = (uint32_t *)&__StackTop;
extern uint32_t __ROM_Start;
extern const fsp_vector_t __VECTOR_TABLE[BSP_CORTEX_VECTOR_TABLE_ENTRIES];

BSP_DONT_REMOVE const fsp_vector_t g_vector_table[BSP_ICU_VECTOR_MAX_ENTRIES] BSP_PLACE_IN_SECTION(BSP_SECTION_APPLICATION_VECTORS) = {
    // you can add interrupt functions here as needed or set them later using NVIC_SetVector()
    // see e.g. ArduinoCore-Renesas vector_table
    [(int)NVIC_ICU_IRQ] = r_icu_isr, 
};
/* Needed to link the NVIC IRQ number to an ICU (interrupt controll unit) event */
/* sets R_ICU->IELSR registers */
const bsp_interrupt_event_t g_interrupt_event_link_select[BSP_ICU_VECTOR_MAX_ENTRIES] = {
    [(int)NVIC_ICU_IRQ] = ELC_EVENT_TO_LINK,
};

// akin to ArduinoCore-Renesas main.cpp
void copy_vectors_to_ram() {
    __disable_irq();
    // reserved space in RAM via linkerscript
    volatile uint32_t *irq_vector_table = (volatile uint32_t *)APPLICATION_VECTOR_TABLE_ADDRESS_RAM;
    size_t _i;
    // copy the Cortex-M4's vectors (ResetHandler, NMI, SysTick, ..)
    for (_i = 0; _i < BSP_CORTEX_VECTOR_TABLE_ENTRIES; _i++) {
        *(irq_vector_table + _i) = (uint32_t)__VECTOR_TABLE[_i];
    }
    // copy the device-specific vectors for this microcontroller (Port interrupts, UART, I2C, ...)
    for (_i = 0; _i < BSP_ICU_VECTOR_MAX_ENTRIES; _i++) {
        *(irq_vector_table + _i + BSP_CORTEX_VECTOR_TABLE_ENTRIES) = (uint32_t)g_vector_table[_i];
    }
    // set vector table offset register to point at our RAM copy
    SCB->VTOR = (uint32_t)irq_vector_table;
    // data sync barrier, renable IRQ
    __DSB();
    __enable_irq();
}

static uint8_t ledState = 0;
static volatile uint8_t interrupt_occurred = 0;
/* Called from icu_irq_isr */
void button_pressed_isr (external_irq_callback_args_t * p_args)
{
    // only flag that interrupt occurred, we can handle debouncing in the main loop
    interrupt_occurred = 1;
}

void hal_entry(void)
{
    // needed when we are invoked from the Arduino bootloader to use our own vector table
    copy_vectors_to_ram();

    // output on LED
    R_IOPORT_PinCfg(&g_ioport_ctrl, LED, IOPORT_CFG_PORT_DIRECTION_OUTPUT);
    // IRQ input + pullup on button (will trigger when touched with GND)
    R_IOPORT_PinCfg(&g_ioport_ctrl, BUTTON, IOPORT_CFG_IRQ_ENABLE | IOPORT_CFG_PORT_DIRECTION_INPUT | IOPORT_CFG_PULLUP_ENABLE);

    external_irq_cfg_t icu_cfg =
    {
        .channel       = ICU_CHANNEL,
        .trigger       = EXTERNAL_IRQ_TRIG_FALLING,
        .filter_enable = false, /* must be 0 for port IRQs */
        .pclk_div      = EXTERNAL_IRQ_PCLK_DIV_BY_64,
        .p_callback    = &button_pressed_isr,
        .p_context     = NULL,
        .ipl           = 0,
        .irq           = (IRQn_Type) NVIC_ICU_IRQ,
    };

    /* Open and enable the external interrupt. */
    icu_instance_ctrl_t irq_ctrl;
    memset(&irq_ctrl, 0, sizeof(irq_ctrl));
    fsp_err_t err = R_ICU_ExternalIrqOpen(&irq_ctrl, &icu_cfg);
    assert(FSP_SUCCESS == err);

    err = R_ICU_ExternalIrqEnable(&irq_ctrl);
    assert(FSP_SUCCESS == err);

    // start with turned on LED
    ledState = 1;
    R_IOPORT_PinWrite(&g_ioport_ctrl, LED, ledState ? BSP_IO_LEVEL_HIGH : BSP_IO_LEVEL_LOW);

    while(true) 
    {
        if(interrupt_occurred) {
            ledState ^= 1; // toggle
            R_IOPORT_PinWrite(&g_ioport_ctrl, LED, ledState ? BSP_IO_LEVEL_HIGH : BSP_IO_LEVEL_LOW);
            // debounce in software
            R_BSP_SoftwareDelay(200, BSP_DELAY_UNITS_MILLISECONDS);
            interrupt_occurred = 0;
        }
    }
}

void R_BSP_WarmStart(bsp_warm_start_event_t event)
{
    if (BSP_WARM_START_RESET == event)
    {
#if BSP_FEATURE_FLASH_LP_VERSION != 0
        /* Enable reading from data flash. */
        R_FACI_LP->DFLCTL = 1U;
        /* Would normally have to wait tDSTOP(6us) for data flash recovery. Placing the enable here, before clock and
         * C runtime initialization, should negate the need for a delay since the initialization will typically take more than 6us. */
#endif
    }
    if (BSP_WARM_START_POST_C == event)
    {
        /* C runtime environment and system clocks are setup. */
        /* E.g., you can configure pins here. */
    }
}
