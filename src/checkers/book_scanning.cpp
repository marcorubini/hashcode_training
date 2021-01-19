#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <vector>
#include <chrono>
#include <unordered_set>
#include <stack>

int B; // number of books
int L; // number of libraries
int D; // number of days
std::vector<int> book_scores;

struct Library {
  int N; // the number of books contained
  int T; // the number of days it takes to finish signup
  int M; // the number of books that can be shipped per day after signup
  std::vector<int> books; 
};

std::vector<Library> libraries;

void assert_reason(bool x, char const* s, auto&&... args) {
  if(!x) {
    char buffer[200];
    snprintf(buffer, 200, s, args...);
    throw std::invalid_argument(buffer);
  }
}

void parse_input() {
  assert_reason(scanf("%d %d %d\n", &B, &L, &D) == 3, 
    "[Input incorrect]: Failed to parse B, L, D.");
  assert_reason(B >= 1 && B <= 100000, 
    "[Input incorrect]: 1 <= B <= 100000, with B = %d.", B);
  assert_reason(L >= 1 && L <= 100000, 
    "[Input incorrect]: 1 <= L <= 100000, with L = %d.", L);
  assert_reason(D >= 1 && D <= 100000, 
    "[Input incorrect]: 1 <= D <= 100000, with D = %d.", D);

  book_scores.resize(B); 
  for(int i=0; i < B; ++i) {
    assert_reason(scanf("%d", &book_scores[i]) == 1,
      "[Input incorrect]: Failed to parse score of book at index %d", i);
    assert_reason(book_scores[i] >= 0 && book_scores[i] <= 100, 
      "[Input incorrect]: 0 <= book_scores[i] <= 100, with i = %d, book_scores[i] = %d", i, book_scores[i]);
  }

  libraries.resize(L);
  for(int i=0; i < L; ++i) {
    assert_reason(scanf("%d %d %d\n", &libraries[i].N, &libraries[i].T, &libraries[i].M) == 3, 
      "[Input incorrect]: Failed to parse N, T, M of library at index %d.", i);
    assert_reason(libraries[i].N >= 1 && libraries[i].N <= 100000,
      "[Input incorrect]: 1 <= libraries[i].N <= 100000, with i = %d, libraries[i].N = %d.", i, libraries[i].N);
    assert_reason(libraries[i].T >= 1 && libraries[i].T <= 100000,
      "[Input incorrect]: 1 <= libraries[i].T <= 100000, with i = %d, libraries[i].T = %d.", i, libraries[i].T);
    assert_reason(libraries[i].M >= 1 && libraries[i].M <= 100000,
      "[Input incorrect]: 1 <= libraries[i].M <= 100000, with i = %d, libraries[i].M = %d.", i, libraries[i].M);

    auto books_set = std::unordered_set<int>();

    libraries[i].books.resize(libraries[i].N);
    for(int j=0; j < libraries[i].N; ++j) {
      assert_reason(scanf("%d", &libraries[i].books[j]) == 1, 
        "[Input incorrect]: Failed to parse book at index %d of library at index %d.", j, i);

      auto id = libraries[i].books[j];

      assert_reason(id >= 0 && id < B, 
        "[Input incorrect]: 0 <= libraries[i].books[j] < B, with i = %d, j = %d, libraries[i].books[j] = %d, B = %d.", i, j, id, B);

      assert_reason(books_set.count(id) == 0,
        "[Input incorrect]: Book at index %d with id %d of library at index %d is duplicate.", j, id, i);

      books_set.insert(id);
    }
  }

  long long total_books = 0;
  for(int i=0; i < L; ++i)
    total_books += libraries[i].N;
  assert_reason(total_books <= 1000000, 
      "[Input incorrect]: Total number of books = %d exceeds 1 million.", total_books);
}

int A; // the number of libraries to sign up

struct signup {
  int Y; // the library to signup
  int K; // the number of books to be scanned
  std::vector<int> books;
};

std::vector<signup> output_libraries;

void parse_output() {
  assert_reason(scanf("%d\n", &A) == 1, 
      "[Output incorrect]: Failed to parse A.");
  assert_reason(A >= 0 && A <= L,
      "[Output incorrect]: 0 <= A <= L, with A = %d, L = %d.", A, L);

  output_libraries.resize(A);
  for(int i=0; i < A; ++i) {
    assert_reason(scanf("%d %d\n", &output_libraries[i].Y, &output_libraries[i].K) == 2,
      "[Output incorrect]: Failed to parse Y and K of library at index %d.", i);

    auto const Y = output_libraries[i].Y;
    auto const K = output_libraries[i].K;

    assert_reason(Y >= 0 && Y < L,
      "[Output incorrect]: 0 <= Y < L, with Y = %d, L = %d.", Y, L);

    auto const N = libraries[Y].N;

    assert_reason(K >= 1 && K <= N,
      "[Output incorrect]: 1 <= K < N, with K = %d, N = %d, Y = %d.", K, N, Y);

    auto scanned_books = std::unordered_set<int>();
    auto scannable = std::unordered_set<int>(libraries[Y].books.begin(), libraries[Y].books.end());

    output_libraries[i].books.resize(K);
    for(int j=0; j < K; ++j) {
      assert_reason(scanf("%d", &output_libraries[i].books[j]) == 1, 
        "[Output incorrect]: Failed to parse book at index %d of library Y = %d.", j, Y);

      auto id = output_libraries[i].books[j];

      assert_reason(scannable.count(id) == 1,
        "[Output incorrect]: Book at index %d with id %d of library Y = %d is not in its original library.", j, id, Y);

      assert_reason(scanned_books.count(id) == 0,
        "[Output incorrect]: Book at index %d with id %d of library Y = %d is duplicate.", j, id, Y);
      scanned_books.insert(id);
    }
  }
}

auto evaluate_output() {
  auto evaluate_signup = [scored_books = std::unordered_set<int>()]
    (int start_time, int Y, std::vector<int>& permutation) mutable {

    int remaining_time = D - (start_time + libraries[Y].T);
    int scanned_books = std::min( (long long)remaining_time * libraries[Y].M, (long long) permutation.size());
    int score = 0;
    for(int i=0; i < scanned_books; ++i) {
      int id = permutation[i];
      if(scored_books.count(id) == 0) {
        score += book_scores[id];
        scored_books.insert(id);
      }
    }
    return score;
  };

  int t = 0;
  int score = 0;
  for(auto& lib : output_libraries) {
    score += evaluate_signup(t, lib.Y, lib.books);
    t += libraries[lib.Y].T;
    if( t >= D )
      break;
  }

  return score;
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

    int score = evaluate_output();
    fprintf(stdout, "%d\n", score);
    fprintf(stderr, "[Output correct]: score = %d.", score);

  } catch(std::invalid_argument& e) {
    fprintf(stdout, "%d\n", 0);
    fprintf(stderr, "%s", e.what());
  }
}
