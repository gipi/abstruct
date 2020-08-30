#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

static void initializa() __attribute__((constructor));
void initializa() {
    printf("hi folks!\n");
}

int main() {
    printf("miao %d\n", errno);
    system("id");

    return 0;
}
