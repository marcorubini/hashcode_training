#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <vector>
#include <chrono>
#include <unordered_set>
#include <stack>
#include <algorithm>

int M; // maximum slices to order
int N; // different types of pizza
std::vector<int> slice_count;

template<class... Args>
void assert_reason(bool x, char const* s, Args&&... args) {
  if(!x) {
    char buffer[200];
    snprintf(buffer, 200, s, args...);
    throw std::invalid_argument(buffer);
  }
}

void parse_input() {
  assert_reason( scanf("%d %d\n", &M, &N) == 2, "[Input incorrect]: Failed to parse M, N.");
  slice_count.resize(N);
  for(int i=0; i < N; ++i) 
    assert_reason(scanf("%d", &slice_count[i]) == 1, 
        "[Input incorrect]:  Failed to parse slice count at index %d.", i);

  for(int i=0; i < N; ++i)
    assert_reason(slice_count[i] <= M,
        "[Input incorrect]: Slice count at index %d is greater than M (%d > %d)", slice_count[i], M);

  assert_reason(std::is_sorted(slice_count.begin(), slice_count.end()), 
      "[Input incorrect]: Slice counts are not sorted.");
}

int K; // the number of different pizza types to order
long long S;
std::vector<int> pizza_types;

void parse_output() {
  assert_reason(scanf("%d\n", &K) == 1, 
      "[Output incorrect]: Failed to parse K.");
  assert_reason(K >= 0 && K < N, 
      "[Output incorrect]: Unsatisfied constraint 0 <= K <= N, with K = %d, N = %d.", K, N);
  pizza_types.resize(K);
  for(int i=0; i < K; ++i)
    assert_reason(scanf("%d", &pizza_types[i]) == 1,
      "[Output incorrect]: Failed to parse the pizza type at index %d.", i);

  for(int i=0; i < K; ++i)
    assert_reason(pizza_types[i] >= 0 && pizza_types[i] < N,
        "[Output incorrect]: Unsatisfied constraint 0 <= pizza_type[i] < N, with i = %d, pizza_type[i] = %d, N = %d.", i, pizza_types[i], N);
  
  auto selected = std::vector<bool>(N);
  for(int i=0; i < K; ++i) {
    assert_reason(selected[pizza_types[i]] == false, "[Output incorrect]: Duplicate pizza type at index %d.", i);
    selected[pizza_types[i]] = true;
  }

  S = 0;
  for(int i=0; i < K; ++i) {
    S += slice_count[pizza_types[i]];
  }
  
  assert_reason(S <= M, "[Output incorrect]: Sum of slice sizes exceedes M, with sum = %d, M = %d.", S, M);
}

auto evaluate_output() {
  return S;
}

int main(int argc, char** argv) {
  if(argc != 4) {
    fprintf(stdout, "%d\n", 0);
    fprintf(stderr, "Incorrect usage, need input and output file.");
    return 0;
  }
  
  try {
    if(!std::freopen(argv[1], "r", stdin)) {
      fprintf(stdout, "%d\n", 0);
      fprintf(stderr, "Input file not found.");
      return 0;
    }

    parse_input();

    if(!std::freopen(argv[3], "r", stdin)) {
      fprintf(stdout, "%d\n", 0);
      fprintf(stderr, "Output file not found.");
      return 0;
    }

    parse_output();

    long long score = evaluate_output();
    fprintf(stdout, "%lld\n", score);
    fprintf(stderr, "[Output correct]: score = %lld.", score);

  } catch(std::invalid_argument& e) {
    fprintf(stdout, "%d\n", 0);
    fprintf(stderr, "%s", e.what());
  }
}
