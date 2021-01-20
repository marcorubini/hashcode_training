#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <vector>
#include <chrono>
#include <unordered_set>
#include <stack>
#include <algorithm>
#include <array>

int M; // Number of pizzas
int T2; // Number of 2-person teams
int T3; // Number of 3-person teams
int T4; // Number of 4-person teams
std::vector<std::vector<std::string>> pizzas;

template<class... Args>
void assert_reason(bool x, char const* s, Args&&... args) {
  if(!x) {
    char buffer[200];
    snprintf(buffer, 200, s, args...);
    throw std::invalid_argument(buffer);
  }
}

void parse_input() {
  assert_reason(scanf("%d %d %d %d\n", &M, &T2, &T3, &T4) == 4, 
      "[Input incorrect]: Failed to parse M, T2, T3, T4.");
  assert_reason(M >= 1 && M <= 100000, "[Input incorrect]: Failed constraint 1 <= M <= 100000, with M = %d.", M);
  assert_reason(T2 >= 0 && T2 <= 100000, "[Input incorrect]: Failed constraint 0 <= T2 <= 50000, with T2 = %d.", T2);
  assert_reason(T3 >= 0 && T3 <= 100000, "[Input incorrect]: Failed constraint 0 <= T3 <= 50000, with T3 = %d.", T3);
  assert_reason(T4 >= 0 && T4 <= 100000, "[Input incorrect]: Failed constraint 0 <= T4 <= 50000, with T4 = %d.", T4);

  pizzas.resize(M);
  for(int i=0; i < M; ++i) {
    int I;
    assert_reason(scanf("%d", &I) == 1, "[Input incorrect]: Failed to parse the number of ingredients of pizza %d.", i);
    assert_reason(I >= 1 && I <= 10000, "[Input incorrect]: The number of ingredients of pizza %d is too large.", i);

    char buffer[30];
    for(int j=0; j < I; ++j) {
      assert_reason(scanf("%20s", buffer) == 1, "[Input incorrect]: Failed to parse ingredient %d of pizza %d.", j, i);
      pizzas[i].emplace_back(buffer);
    }
  }
}

int D; // The number of deliveries

struct delivery {
  int L;
  std::vector<int> pizzas;
};

std::vector<delivery> deliveries;

void parse_output() {
  assert_reason(scanf("%d\n", &D) == 1, "[Output incorrect]: Failed to parse D.");
  assert_reason(D >= 1 && D <= T2 + T3 + T4, "[Output incorrect]: Failed constraint 1 <= D <= T2 + T3 + T4, with D = %d", D);
  deliveries.resize(D);
  
  auto counters = std::array<int, 3> {T2, T3, T4};
  auto delivered = std::vector<bool>(M, false);

  for(int i=0; i < D; ++i) {
    assert_reason(scanf("%d", &deliveries[i].L) == 1, "[Output incorrect]: Failed to parse L for delivery %d.", i);
    auto& d = deliveries[i];
    assert_reason(d.L >= 2 && d.L <= 4, 
        "[Output incorrect]: Failed constraint 2 <= L <= 4 for delivery at index %d, with L = %d.", i, d.L);

    counters[d.L-2] -= 1;
    assert_reason(counters[d.L-2] >= 0,
        "[Output incorrect]: Invalid delivery at index %d. Too many deliveries for teams of size %d.", i, d.L);

    d.pizzas.resize(d.L);
    for(int j=0; j < d.L; ++j) {
      assert_reason(scanf("%d", &d.pizzas[j]) == 1, 
          "[Output incorrect]: Invalid delivery at index %d. Failed to parse pizza at index %d.", i, j);
    }

    for(int x : d.pizzas) {
      assert_reason(x >= 0 && x < M, 
          "[Output incorrect]: Invalid delivery at index %d. Invalid pizza index %d.", i, x);
      assert_reason(delivered[x] == false, 
          "[Output incorrect]: Invalid delivery at index %d. Pizza %d was delivered twice.", i, x);
      delivered[x] = true;
    }
  }
}

auto evaluate_output() {
  long long total_score = 0;
    
  std::unordered_set<std::string> ingredients;
  for(auto& d : deliveries ) {
    for(int p : d.pizzas)
      for(std::string& s : pizzas[p])
        ingredients.insert(s);

    long long unique_ingredients = ingredients.size();
    long long delivery_score = unique_ingredients * unique_ingredients;
    total_score += delivery_score;
    ingredients.clear();
  }

  return total_score;
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
