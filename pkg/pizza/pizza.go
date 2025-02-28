// Package pizza provides functionality for creating and managing pizza orders.
package pizza

import (
	"errors"
	"time"
)

type PizzaType string

const (
	Margherita PizzaType = "margherita"
	Pepperoni  PizzaType = "pepperoni"
	Hawaiian   PizzaType = "hawaiian"
)

type Pizza struct {
	Type     PizzaType
	SizeInch int
	BakedAt  *time.Time
}

type Order struct {
	ID        string
	PizzaType PizzaType
	SizeInch  int
	Status    string
	CreatedAt time.Time
}

// NewOrder creates a new pizza order with the specified type and size.
// It returns an error if the size is outside the valid range (8-24 inches)
// or if the pizza type is invalid.
func NewOrder(pizzaType PizzaType, sizeInch int) (*Order, error) {
	if sizeInch < 8 {
		return nil, errors.New("minimum size is 8 inches")
	}

	if sizeInch > 24 {
		return nil, errors.New("maximum size is 24 inches")
	}

	switch pizzaType {
	case Margherita, Pepperoni:
		// Valid pizza types
	default:
		return nil, errors.New("invalid pizza type")
	}

	return &Order{
		ID:        generateOrderID(),
		PizzaType: pizzaType,
		SizeInch:  sizeInch,
		Status:    "pending",
		CreatedAt: time.Now(),
	}, nil
}

// generateOrderID creates a unique order ID based on the current timestamp
// in the format "YYYYMMDDhhmmss".
func generateOrderID() string {
	return time.Now().Format("20060102150405")
}

// CalculatePrice determines the price of the pizza based on its size and type.
// The base price is $1 per inch of diameter with premiums applied for specialty types:
// - Pepperoni: 20% premium
// - Hawaiian: 30% premium
// - Margherita: no premium (base price)
func (o *Order) CalculatePrice() float64 {
	basePrice := float64(o.SizeInch) * 1.0 // $1 per inch of diameter
	switch o.PizzaType {
	case Pepperoni:
		return basePrice * 1.2 // 20% premium for pepperoni
	case Hawaiian:
		return basePrice * 1.3 // 30% premium for hawaiian
	default:
		return basePrice
	}
}

// CalculateCringeLevel determines the cringe level of an array of orders based on the pizzas size and types.
// Only Hawaiian pizzas are cringe. The level grows linearly with the size of the pizza.
// Homever, a combination of Hawaiin and Papperoni is super cringe: If present, it will triple the cringe level.
func (o *Order) CalculateCringeLevel() int {
	if o.PizzaType == Hawaiian {
		return o.SizeInch
	}
	return 0
}
