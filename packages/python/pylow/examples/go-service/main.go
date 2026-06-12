package main

import (
	"fmt"
	"net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello from Go Service!")
}

func main() {
	http.HandleFunc("/", helloHandler)
	fmt.Println("Starting Go service on port 8080...")
	http.ListenAndServe(":8080", nil)
}
