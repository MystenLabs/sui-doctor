#include <stdio.h>
#include <stdlib.h>
#include <time.h>

unsigned long fibonacci(unsigned long n) {
    if (n == 0 || n == 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

void benchmark_fibonacci(int iterations) {
    printf("Running Test 1...\n");

    // Calculate fibonacci (single core check)
    double total_time = 0.0;
    for (int i = 0; i < iterations; i++) {
        clock_t start = clock();
        fibonacci(45);
        clock_t end = clock();
        total_time += ((double)(end - start)) / CLOCKS_PER_SEC;
    }
    double average_time = total_time / iterations;

    printf("Test 1: average time taken: %f seconds\n", average_time);
}

void benchmark_gzip(int iterations) {
    printf("\nRunning Test 2...\n");

    double total_time = 0.0;
    for (int i = 0; i < iterations; i++) {

        // since a child process is created using the clock() won't be accurate anymore as clock() measures the CPU
        // spent time by the program it self, so any actual spent time from the child process will not be taken into account.
        // Thus we switch to using the actual wall time instead for this benchmark.
        struct timespec start, end;
        clock_gettime(CLOCK_MONOTONIC_RAW, &start);

        // Stress test by generating random data of 256MB and passing to compress.
        int status = system("head  -c 268435456 /dev/urandom | gzip > /dev/null");
        if (status == -1) {
            printf("Test 2: failed to run, will exclude from benchmarking");
            return;
        }

        clock_gettime(CLOCK_MONOTONIC_RAW, &end);

        total_time += (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1000000000.0;
    }
    double average_time = total_time / iterations;

    printf("Test 2: average time taken: %f seconds\n", average_time);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: <test_1_iterations> <test_2_iterations>\n");
        return 1;
    }

    benchmark_fibonacci(atoi(argv[1]));
    benchmark_gzip(atoi(argv[2]));

    return 0;
}