package pasta

import (
	"testing"
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
