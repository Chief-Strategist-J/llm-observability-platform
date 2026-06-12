package com.example.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.*;

@RestController
public class AlgorithmController {

    // 1. Recursive Fibonacci: Ideal for demonstrating call stacks in `pylow calltree`
    @GetMapping("/fibonacci")
    public Map<String, Object> fibonacci(@RequestParam(defaultValue = "10") int n) {
        long startTime = System.nanoTime();
        long result = calculateFibonacci(n);
        long durationMs = (System.nanoTime() - startTime) / 1_000_000;

        Map<String, Object> response = new HashMap<>();
        response.put("algorithm", "Recursive Fibonacci");
        response.put("input", n);
        response.put("result", result);
        response.put("duration_ms", durationMs);
        return response;
    }

    private long calculateFibonacci(int n) {
        if (n <= 1) {
            return n;
        }
        return calculateFibonacci(n - 1) + calculateFibonacci(n - 2);
    }

    // 2. Custom QuickSort: Ideal for tracking array swapping state in `pylow debug-steps`
    @GetMapping("/sort")
    public Map<String, Object> sort(@RequestParam(defaultValue = "9,3,7,5,6,4,8,2") String items) {
        String[] parts = items.split(",");
        int[] array = new int[parts.length];
        for (int i = 0; i < parts.length; i++) {
            array[i] = Integer.parseInt(parts[i].trim());
        }

        int[] original = array.clone();
        quickSort(array, 0, array.length - 1);

        Map<String, Object> response = new HashMap<>();
        response.put("algorithm", "QuickSort");
        response.put("input", original);
        response.put("sorted", array);
        return response;
    }

    private void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high);
            quickSort(arr, low, pi - 1);
            quickSort(arr, pi + 1, high);
        }
    }

    private int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = (low - 1);
        for (int j = low; j < high; j++) {
            if (arr[j] < pivot) {
                i++;
                // Swap arr[i] and arr[j]
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
        // Swap arr[i+1] and arr[high] (or pivot)
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;

        return i + 1;
    }

    // 3. Grid Pathfinding (BFS): Good for tracking queue traversals and graph algorithms
    @GetMapping("/pathfind")
    public Map<String, Object> pathfind(
            @RequestParam(defaultValue = "0") int startX,
            @RequestParam(defaultValue = "0") int startY,
            @RequestParam(defaultValue = "4") int targetX,
            @RequestParam(defaultValue = "4") int targetY) {

        // 5x5 grid with obstacles (1 = obstacle, 0 = open path)
        int[][] grid = {
            {0, 0, 0, 1, 0},
            {1, 1, 0, 1, 0},
            {0, 0, 0, 0, 0},
            {0, 1, 1, 1, 0},
            {0, 0, 0, 0, 0}
        };

        List<String> path = findPathBFS(grid, startX, startY, targetX, targetY);

        Map<String, Object> response = new HashMap<>();
        response.put("algorithm", "Grid BFS Pathfinding");
        response.put("grid_size", "5x5");
        response.put("start", startX + "," + startY);
        response.put("target", targetX + "," + targetY);
        response.put("path", path);
        response.put("path_found", !path.isEmpty());
        return response;
    }

    private List<String> findPathBFS(int[][] grid, int startX, int startY, int targetX, int targetY) {
        int rows = grid.length;
        int cols = grid[0].length;

        if (grid[startX][startY] == 1 || grid[targetX][targetY] == 1) {
            return Collections.emptyList();
        }

        Queue<Node> queue = new LinkedList<>();
        boolean[][] visited = new boolean[rows][cols];

        queue.add(new Node(startX, startY, null));
        visited[startX][startY] = true;

        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}}; // Up, Down, Left, Right

        Node targetNode = null;
        while (!queue.isEmpty()) {
            Node current = queue.poll();

            if (current.x == targetX && current.y == targetY) {
                targetNode = current;
                break;
            }

            for (int[] dir : directions) {
                int nextX = current.x + dir[0];
                int nextY = current.y + dir[1];

                if (nextX >= 0 && nextX < rows && nextY >= 0 && nextY < cols 
                        && grid[nextX][nextY] == 0 && !visited[nextX][nextY]) {
                    visited[nextX][nextY] = true;
                    queue.add(new Node(nextX, nextY, current));
                }
            }
        }

        if (targetNode == null) {
            return Collections.emptyList();
        }

        // Reconstruct path
        List<String> path = new ArrayList<>();
        Node temp = targetNode;
        while (temp != null) {
            path.add("(" + temp.x + "," + temp.y + ")");
            temp = temp.parent;
        }
        Collections.reverse(path);
        return path;
    }

    private static class Node {
        int x, y;
        Node parent;

        Node(int x, int y, Node parent) {
            this.x = x;
            this.y = y;
            this.parent = parent;
        }
    }
}
