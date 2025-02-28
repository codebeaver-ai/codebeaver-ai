package pasta

import (
	"errors"
	"time"
)

type PastaType string

const (
	Spaghetti    PastaType = "spaghetti"
	Penne        PastaType = "penne"
	Fettuccine   PastaType = "fettuccine"
)

type Pasta struct {
	Type        PastaType
	WeightGrams int
	CookedAt    *time.Time
}

type Order struct {
	ID          string
	PastaType   PastaType
	WeightGrams int
	Status      string
	CreatedAt   time.Time
}

func NewOrder(pastaType PastaType, weightGrams int) (*Order, error) {
	if weightGrams < 100 {
		return nil, errors.New("minimum order is 100 grams")
	}

	if weightGrams > 5000 {
		return nil, errors.New("maximum order is 5000 grams")
	}

	switch pastaType {
	case Spaghetti, Penne, Fettuccine:
		// Valid pasta types
	default:
		return nil, errors.New("invalid pasta type")
	}

	return &Order{
		ID:          generateOrderID(),
		PastaType:   pastaType,
		WeightGrams: weightGrams,
		Status:      "pending",
		CreatedAt:   time.Now(),
	}, nil
}

func generateOrderID() string {
	return time.Now().Format("20060102150405")
}

func (o *Order) CalculatePrice() float64 {
	basePrice := float64(o.WeightGrams) * 0.01 // 1 cent per gram
	switch o.PastaType {
	case Fettuccine:
		return basePrice * 1.2 // 20% premium for fancy pasta
	default:
		return basePrice
	}
} 