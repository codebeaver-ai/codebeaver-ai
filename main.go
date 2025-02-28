package main

import (
	"log"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/yourusername/pasta-factory/api"
)

func main() {
	r := mux.NewRouter()

	r.HandleFunc("/orders", api.CreateOrder).Methods("POST")

	log.Printf("Starting server on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatal(err)
	}
} 