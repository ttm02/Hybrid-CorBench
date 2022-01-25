#include "nondeterminism.h"

#include <mpi.h>
#include <stdlib.h>

// Data race due to thread-unsafe MPI_Probe use:
// Process 0 with 2 Threads sense different data with the same envelope.
// Process 1 uses MPI_Probe (marker "A") to allocate the required receive buffer dynamically.
// Between Probe ("A"), MPI_Get_count and the posted MPI_Recv (marker "B"), the message may "change",
// as the other thread may also probe (and receive) the message.

#define NUM_THREADS 2

int main(int argc, char *argv[]) {
  int provided;
  const int requested = MPI_THREAD_MULTIPLE;

  MPI_Init_thread(&argc, &argv, requested, &provided);
  if (provided < requested) {
    has_error_manifested(false);
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
  }

  int size;
  int rank;
  MPI_Comm_size(MPI_COMM_WORLD, &size);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);

  bool has_race = false;

#pragma omp parallel num_threads(NUM_THREADS)
  {
    if (rank == 0) {
#pragma omp sections
      {
#pragma omp section
        {
          int value[2] = {-2, -2};
          MPI_Send(value, 2, MPI_INT, 1, 0, MPI_COMM_WORLD);
        }
#pragma omp section
        {
          int value = -1;
          MPI_Send(&value, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
        }
      }

    } else if (rank == 1) {
      MPI_Status status;

      MPI_Probe(0, MPI_ANY_TAG, MPI_COMM_WORLD, &status); /* A */

      DISTURB_THREAD_ORDER
      int count;
      MPI_Get_count(&status, MPI_INT, &count);

      int *value = (int *)malloc(sizeof(int) * count);
      MPI_Recv(value, count, MPI_INT, 0, status.MPI_TAG, MPI_COMM_WORLD, MPI_STATUS_IGNORE); /* B */

      const bool thread_race = (count == 1 && value[0] != -1) || (count == 2 && value[0] != -2);

#pragma omp critical
      has_race = (has_race || thread_race);

      //#pragma omp critical
      //      printf("Status race %i: %i %i\n", has_race, count, value[0]);
      // sometimes:
      //      Status race 0: 2 -2
      //      Status race 0: 1 -1
      // often:
      //      Status race 0: 2 -2
      //      Status race 1: 2 -1

      free(value);
    }
  }

  has_error_manifested(has_race);
  if (has_race)
    printf("Has race\n");

  MPI_Finalize();
  return 0;
}
