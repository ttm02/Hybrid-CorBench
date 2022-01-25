#include "nondeterminism.h"

#include <mpi.h>
#include <stdlib.h>

// Data Race on buffer: Concurrently, (omp) task A writes to the buffer (marker "A") and another task executes a
// bcast operation using the buffer (marker "B").

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

  int send_data[BUFFER_LENGTH_INT];

  fill_message_buffer(send_data, BUFFER_LENGTH_BYTE, 2);

  if (rank == 0) {
#pragma omp parallel num_threads(NUM_THREADS)
    {
#pragma omp single
      {
#pragma omp task depend(out : send_data)  // fix for data race: depend(out : send_data)
        {
#ifdef USE_DISTURBED_THREAD_ORDER
          us_sleep(10);  // Data race is very rare otherwise
#endif
          fill_message_buffer(send_data, BUFFER_LENGTH_BYTE, 6); /* A */
        }
#pragma omp task depend(in : send_data)  // fix for data race: depend(in : send_data)
        { MPI_Bcast(send_data, BUFFER_LENGTH_INT, MPI_INT, 0, MPI_COMM_WORLD); /* B */ }
      }
    }
  } else {
    MPI_Bcast(send_data, BUFFER_LENGTH_INT, MPI_INT, 0, MPI_COMM_WORLD);
  }

  const bool error = !has_buffer_expected_content(send_data, BUFFER_LENGTH_BYTE, 6);
  has_error_manifested(error);

  MPI_Finalize();

  return 0;
}
