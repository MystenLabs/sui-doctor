#include <stdio.h>
#include <time.h>
#include <stdbool.h>

unsigned long fibonacci(unsigned long n) {
    if (n == 0 || n == 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

bool benchmark_fibonacci(int iterations) {
    double const AVERAGE_RUN_TIME = 6.6;

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

    if (average_time > AVERAGE_RUN_TIME) {
        printf("Test 1: average time is higher than expected average %fs > %fs\n", average_time, AVERAGE_RUN_TIME);
        return false;
    } else {
        printf("Test 1: average time taken: %f seconds\n", average_time);
        return true;
    }
}

unsigned long factorial(unsigned long n) {
    long x = 1;
    for (unsigned long i = 1; i < n; i++) {
        x *= i;
    }
    return x;
}

bool benchmark_factorial(int iterations) {
    double const AVERAGE_RUN_TIME = 0.1;

    printf("\nRunning Test 2...\n");

    // Calculate factorial (single core check)
    double total_time = 0.0;
    for (int i = 0; i < iterations; i++) {
        clock_t start = clock();
        factorial(100000000);
        clock_t end = clock();
        total_time += ((double)(end - start)) / CLOCKS_PER_SEC;
    }
    double average_time = total_time / iterations;

    if (average_time > AVERAGE_RUN_TIME) {
        printf("Test 2: average time is higher than expected average %fs > %fs\n", average_time, AVERAGE_RUN_TIME);
        return false;
    } else {
        printf("Test 2: average time taken: %f seconds\n", average_time);
        return true;
    }
}

int main() {
    bool test_1_passed = benchmark_fibonacci(10);
    bool test_2_passed = benchmark_factorial(20);

    printf("CPU speed check passed: %9s\n", (test_1_passed && test_2_passed) ? "yes" : "no");

    return 0;
}