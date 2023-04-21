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

unsigned long factorial(unsigned long n) {
    long x = 1;
    for (unsigned long i = 1; i < n; i++) {
        x *= i;
    }
    return x;
}

void benchmark_factorial(int iterations) {
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

    printf("Test 2: average time taken: %f seconds\n", average_time);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: <test_1_iterations> <test_2_iterations>\n");
        return 1;
    }

    benchmark_fibonacci(atoi(argv[1]));
    benchmark_factorial(atoi(argv[2]));

    return 0;
}