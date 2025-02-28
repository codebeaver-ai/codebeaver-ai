package api

import (
	"encoding/json"
	"net/http"

	"github.com/yourusername/pasta-factory/pkg/pasta"
	"github.com/yourusername/pasta-factory/pkg/pizza"
)

type OrderRequest struct {
	PastaType     string `json:"pasta_type"`
	WeightGrams   int    `json:"weight_grams"`
	PizzaType     string `json:"pizza_type,omitempty"`
	PizzaSizeInch int    `json:"pizza_size_inch,omitempty"`
}

type OrderResponse struct {
	OrderID       string  `json:"order_id"`
	PastaType     string  `json:"pasta_type"`
	WeightGrams   int     `json:"weight_grams"`
	Price         float64 `json:"price"`
	Status        string  `json:"status"`
	PizzaType     string  `json:"pizza_type,omitempty"`
	PizzaSizeInch int     `json:"pizza_size_inch,omitempty"`
	PizzaPrice    float64 `json:"pizza_price,omitempty"`
}

func CreateOrder(w http.ResponseWriter, r *http.Request) {
	var req OrderRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	resp := OrderResponse{}
	totalPrice := 0.0

	if req.PastaType != "" {
		pastaOrder, err := pasta.NewOrder(pasta.PastaType(req.PastaType), req.WeightGrams)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		pastaPrice := pastaOrder.CalculatePrice()
		totalPrice += pastaPrice

		resp.OrderID = pastaOrder.ID
		resp.PastaType = string(pastaOrder.PastaType)
		resp.WeightGrams = pastaOrder.WeightGrams
		resp.Price = pastaPrice
		resp.Status = pastaOrder.Status
	}

	if req.PizzaType != "" {
		pizzaOrder, err := pizza.NewOrder(pizza.PizzaType(req.PizzaType), req.PizzaSizeInch)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		pizzaPrice := pizzaOrder.CalculatePrice()
		totalPrice += pizzaPrice

		if resp.OrderID == "" {
			resp.OrderID = pizzaOrder.ID
			resp.Status = pizzaOrder.Status
		}
		resp.PizzaType = string(pizzaOrder.PizzaType)
		resp.PizzaSizeInch = pizzaOrder.SizeInch
		resp.PizzaPrice = pizzaPrice
	}

	if resp.OrderID == "" {
		http.Error(w, "Order must include at least pasta or pizza", http.StatusBadRequest)
		return
	}

	if resp.PastaType != "" && resp.PizzaType != "" {
		resp.Price = totalPrice
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
