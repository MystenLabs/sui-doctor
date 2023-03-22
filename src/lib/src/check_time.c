
/*
 * Code from: https://stackoverflow.com/questions/65342065/how-do-i-check-whether-my-systems-clock-is-synchronized-to-a-ntp-server
 */

#include <stdio.h>
#include <sys/timex.h>

int main()
{
    struct timex timex_info = {};
    timex_info.modes = 0;         /* explicitly don't adjust any time parameters */

    int ntp_result = ntp_adjtime(&timex_info);

    printf("Max       error: %9ld (us)\n", timex_info.maxerror);
    printf("Estimated error: %9ld (us)\n", timex_info.esterror);
    printf("Clock precision: %9ld (us)\n", timex_info.precision);
    printf("Jitter:          %9ld (%s)\n", timex_info.jitter,
           (timex_info.status & STA_NANO) ? "ns" : "us");
    printf("Synchronized:    %9s\n",
           (ntp_result >= 0 && ntp_result != TIME_ERROR) ? "yes" : "no");
    return 0;
}

