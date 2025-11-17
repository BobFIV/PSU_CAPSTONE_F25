#include "main.h"

/* LED control variables */
const struct device *led_pwm;
int16_t current_brightness = 0;
bool brightness_increasing = true;
struct k_timer led_timer;
struct k_work led_work;
bool led_blink_state = false;
uint8_t blink_count = 0;



/* LED control function implementations */
void led_work_handler(struct k_work *work)
{
	if (conn_count == 0) {
		/* Breathing effect when no devices connected */
		if (brightness_increasing) {
			current_brightness += 5;
			if (current_brightness >= MAX_BRIGHTNESS) {
				current_brightness = MAX_BRIGHTNESS;
				brightness_increasing = false;
			}
		} else {
			current_brightness -= 5;
			if (current_brightness <= 0) {
				current_brightness = 0;
				brightness_increasing = true;
			}
		}
		
		/* Set PWM brightness for LED1 (pwm-led0, index 0) */
		if (led_pwm && device_is_ready(led_pwm)) {
			led_set_brightness(led_pwm, 0, current_brightness);
		} else {
			/* Fallback to GPIO LED - simple on/off for breathing effect */
			if (current_brightness > 50) {
				dk_set_led_on(CON_STATUS_LED);
			} else {
				dk_set_led_off(CON_STATUS_LED);
			}
		}
	} else {
		/* Blinking effect based on device count */
		if (led_blink_state) {
			/* Turn LED on */
			if (led_pwm && device_is_ready(led_pwm)) {
				led_set_brightness(led_pwm, 0, MAX_BRIGHTNESS);
			} else {
				dk_set_led_on(CON_STATUS_LED);
			}
			led_blink_state = false;
			/* Schedule next blink */
			k_timer_start(&led_timer, K_MSEC(BLINK_DURATION), K_NO_WAIT);
		} else {
			/* Turn LED off */
			if (led_pwm && device_is_ready(led_pwm)) {
				led_set_brightness(led_pwm, 0, 0);
			} else {
				dk_set_led_off(CON_STATUS_LED);
			}
			led_blink_state = true;
			blink_count++;
			
			if (blink_count >= conn_count) {
				/* Finished blinking for all devices, wait 2 seconds */
				blink_count = 0;
				k_timer_start(&led_timer, K_MSEC(BLINK_INTERVAL), K_NO_WAIT);
			} else {
				/* Continue blinking */
				k_timer_start(&led_timer, K_MSEC(BLINK_DURATION), K_NO_WAIT);
			}
		}
	}
}

void led_timer_handler(struct k_timer *timer)
{
	k_work_submit(&led_work);
}

void start_led_breathing(void)
{
	stop_led_effects();
	current_brightness = 0;
	brightness_increasing = true;
	k_timer_start(&led_timer, K_MSEC(PWM_FADE_DELAY), K_MSEC(PWM_FADE_DELAY));
}

void start_led_blinking(uint8_t device_count)
{
	stop_led_effects();
	blink_count = 0;
	led_blink_state = true;
	/* Start first blink immediately */
	k_work_submit(&led_work);
}

void stop_led_effects(void)
{
	k_timer_stop(&led_timer);
	blink_count = 0;
	led_blink_state = false;
}

void flash_data_led(void)
{
	/* Flash LED2 briefly to indicate data reception */
	dk_set_led_on(DK_LED2);
	k_sleep(K_MSEC(50));  /* 50ms flash */
	dk_set_led_off(DK_LED2);
}
