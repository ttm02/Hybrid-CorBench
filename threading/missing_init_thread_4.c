#include "nondeterminism.h"
#include <mpi.h>
#include <omp.h>
#include <stddef.h>
#include <stdio.h>

/*
 * A Threaded Program need to use MPI_Init_Thread
 */
int main(int argc, char *argv[]) {
  int myRank;
  int buffer_out[10], buffer_in[10];

  MPI_Init(&argc, &argv);
  MPI_Comm_rank(MPI_COMM_WORLD, &myRank);

#pragma omp parallel num_threads(NUM_THREADS)
  {
#pragma omp for
    for (int i = 0; i < 10; i++) {
      buffer_out[i] = i * 10;
    }
// implicit OpenMP barrier
#pragma omp sections
    {
#pragma omp section
      {
        if (myRank == 0) {
          MPI_Send(buffer_out, 10, MPI_INT, 1, 123, MPI_COMM_WORLD);
        } else if (myRank == 1) {
          MPI_Recv(buffer_in, 10, MPI_INT, 0, 123, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
      }
#pragma omp section
      if (myRank == 1) {
        MPI_Send(buffer_out, 10, MPI_INT, 0, 123, MPI_COMM_WORLD);
      } else if (myRank == 0) {
        MPI_Recv(buffer_in, 10, MPI_INT, 1, 123, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
      }
    }
  }

  if (myRank == 0) {
    MPI_Send(buffer_out, 10, MPI_INT, 1, 123, MPI_COMM_WORLD);
  } else if (myRank == 1) {
    MPI_Recv(buffer_in, 10, MPI_INT, 0, 123, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
  }

  has_error_manifested(NUM_THREADS > 1);
  MPI_Finalize();

  return 0;
}
