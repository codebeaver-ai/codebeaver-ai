package pasta

import (
    "testing"
    "time"
)

func TestNewOrder(t *testing.T) {
    tests := []struct {
    name        string
    pastaType   PastaType
    weightGrams int
    wantErr     bool
    }{
    {
    name:        "valid order",
    pastaType:   Spaghetti,
    weightGrams: 500,
    wantErr:     false,
    },
    {
    name:        "too small order",
    pastaType:   Penne,
    weightGrams: 50,
    wantErr:     true,
    },
    {
    name:        "too large order",
    pastaType:   Fettuccine,
    weightGrams: 6000,
    wantErr:     true,
    },
    {
    name:        "invalid pasta type",
    pastaType:   "lasagna",
    weightGrams: 500,
    wantErr:     true,
    },
    }

    for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
    order, err := NewOrder(tt.pastaType, tt.weightGrams)
    if (err != nil) != tt.wantErr {
    t.Errorf("NewOrder() error = %v, wantErr %v", err, tt.wantErr)
    return
    }
    if !tt.wantErr && order == nil {
    t.Error("NewOrder() returned nil order when no error expected")
    }
    })
    }
}

func TestCalculatePrice(t *testing.T) {
    // This test verifies that CalculatePrice returns the correct price for both standard and premium pasta.
    // A standard pasta (e.g. spaghetti) should be priced at 1 cent per gram,
    // while a premium pasta (fettuccine) receives a 20% price increase.

    // Test with standard pasta: Spaghetti with weight 1000 grams.
    orderStandard, err := NewOrder(Spaghetti, 1000)
    if err != nil {
    t.Fatalf("unexpected error creating standard order: %v", err)
    }
    priceStandard := orderStandard.CalculatePrice()
    expectedStandard := 1000 * 0.01 // 1 cent per gram
    if priceStandard != expectedStandard {
    t.Errorf("CalculatePrice() for standard pasta: got %v, want %v", priceStandard, expectedStandard)
    }

    // Test with premium pasta: Fettuccine with weight 1000 grams.
    orderPremium, err := NewOrder(Fettuccine, 1000)
    if err != nil {
    t.Fatalf("unexpected error creating premium order: %v", err)
    }
    pricePremium := orderPremium.CalculatePrice()
    expectedPremium := 1000 * 0.01 * 1.2 // 20% premium for Fettuccine
    if pricePremium != expectedPremium {
    t.Errorf("CalculatePrice() for premium pasta: got %v, want %v", pricePremium, expectedPremium)
    }
}
// TestOrderBoundaryValues tests the creation of orders with boundary weight values,
func TestOrderBoundaryValues(t *testing.T) {
    // Lower boundary test: exactly 100 grams with standard pasta (Spaghetti)
    orderLow, err := NewOrder(Spaghetti, 100)
    if err != nil {
        t.Errorf("Expected no error for a 100 grams order, got: %v", err)
    }
    if orderLow.WeightGrams != 100 {
        t.Errorf("Expected order weight to be 100, got: %d", orderLow.WeightGrams)
    }

    // Upper boundary test: exactly 5000 grams with premium pasta (Fettuccine)
    orderHigh, err := NewOrder(Fettuccine, 5000)
    if err != nil {
        t.Errorf("Expected no error for a 5000 grams order, got: %v", err)
    }
    if orderHigh.WeightGrams != 5000 {
        t.Errorf("Expected order weight to be 5000, got: %d", orderHigh.WeightGrams)
    }

    // Verify that the premium price calculation is correct for 5000 grams of Fettuccine.
    priceHigh := orderHigh.CalculatePrice()
    expectedPrice := 5000 * 0.01 * 1.2 // price with 20% premium
    if priceHigh != expectedPrice {
        t.Errorf("Expected price: %v, got: %v", expectedPrice, priceHigh)
    }

    // Check that the generated order IDs follow the expected 14-digit timestamp format.
    if len(orderLow.ID) != 14 {
        t.Errorf("Expected orderLow ID to be 14 characters long, got: %s", orderLow.ID)
    }
    if len(orderHigh.ID) != 14 {
        t.Errorf("Expected orderHigh ID to be 14 characters long, got: %s", orderHigh.ID)
    }
}

func TestOrderCreationFields(t *testing.T) {
    order, err := NewOrder(Spaghetti, 1000)
    if err != nil {
        t.Fatalf("unexpected error creating order: %v", err)
    }

    // Verify that the order status is set to "pending"
    if order.Status != "pending" {
        t.Errorf("expected order status 'pending', got '%s'", order.Status)
    }

    // Verify that CreatedAt is properly initialized (non-zero and recent)
    if order.CreatedAt.IsZero() {
        t.Error("expected CreatedAt to be initialized, but it was zero")
    }

    now := time.Now()
    if now.Sub(order.CreatedAt) > 2*time.Second {
        t.Error("order CreatedAt timestamp is not recent")
    }

    // Verify that the order ID has the expected 14 character format (timestamp)
    if len(order.ID) != 14 {
        t.Errorf("expected order ID of length 14, got %d", len(order.ID))
    }
}
// TestUniqueOrderIDs verifies that sequential orders generate unique IDs by ensuring that
// the timestamp-based order ID from generateOrderID is different between two orders created at different times.
func TestUniqueOrderIDs(t *testing.T) {
    order1, err := NewOrder(Spaghetti, 500)
    if err != nil {
        t.Fatalf("unexpected error creating order1: %v", err)
    }
    // Sleep for slightly more than 1 second to guarantee a different timestamp for the next order.
    time.Sleep(1100 * time.Millisecond)
    order2, err := NewOrder(Penne, 500)
    if err != nil {
        t.Fatalf("unexpected error creating order2: %v", err)
    }
    if order1.ID == order2.ID {
        t.Errorf("expected unique order IDs, but got the same ID: %s", order1.ID)
    }
}