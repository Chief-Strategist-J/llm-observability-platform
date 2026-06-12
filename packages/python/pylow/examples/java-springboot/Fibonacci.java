public class Fibonacci {
    public static void main(String[] args) {
        int n = 6;
        int result = calculate(n);
        System.out.println("Fibonacci of " + n + " is " + result);
    }

    public static int calculate(int n) {
        if (n <= 1) {
            return n;
        }
        return calculate(n - 1) + calculate(n - 2);
    }
}
