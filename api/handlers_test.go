package api

import (
    "bytes"
    "encoding/json"
    "io/ioutil"
    "net/http"
    "net/http/httptest"
    "testing"
)

// TestCreateOrder tests the CreateOrder handler with various scenarios including invalid JSON,
// missing both order types, and valid orders for pasta only, pizza only, and combined orders.
func TestCreateOrder(t *testing.T) {
    tests := []struct {
    name           string
    input          interface{}
    expectedStatus int
    expectedError  string
    check          func(t *testing.T, body []byte)
    }{
    {
    name:           "Invalid JSON",
    input:          "invalid json",
    expectedStatus: http.StatusBadRequest,
    expectedError:  "Invalid request body",
    },
    {
    name:           "Missing both pasta and pizza",
    input:          map[string]interface{}{},
    expectedStatus: http.StatusBadRequest,
    expectedError:  "Order must include at least pasta or pizza",
    },
    {
    name:  "Pasta only order",
    input: map[string]interface{}{"pasta_type": "spaghetti", "weight_grams": 300},
    // expecting success so check that OrderID and PastaType are set correctly.
    expectedStatus: http.StatusOK,
    check: func(t *testing.T, body []byte) {
    var resp OrderResponse
    if err := json.Unmarshal(body, &resp); err != nil {
        t.Errorf("failed to unmarshal response: %v", err)
    }
    if resp.OrderID == "" {
        t.Error("expected OrderID not to be empty")
    }
    if resp.PastaType != "spaghetti" {
        t.Errorf("expected pasta_type to be 'spaghetti', got '%s'", resp.PastaType)
    }
    if resp.Status == "" {
        t.Error("expected status to be set")
    }
    },
    },
    {
    name:  "Pizza only order",
    input: map[string]interface{}{"pizza_type": "margherita", "pizza_size_inch": 12},
    expectedStatus: http.StatusOK,
    check: func(t *testing.T, body []byte) {
    var resp OrderResponse
    if err := json.Unmarshal(body, &resp); err != nil {
        t.Errorf("failed to unmarshal response: %v", err)
    }
    if resp.OrderID == "" {
        t.Error("expected OrderID not to be empty")
    }
    if resp.PizzaType != "margherita" {
        t.Errorf("expected pizza_type to be 'margherita', got '%s'", resp.PizzaType)
    }
    if resp.Status == "" {
        t.Error("expected status to be set")
    }
    },
    },
    {
    name: "Combined pasta and pizza order",
    input: map[string]interface{}{
    "pasta_type":      "penne",
    "weight_grams":    400,
    "pizza_type":      "pepperoni",
    "pizza_size_inch": 14,
    },
    expectedStatus: http.StatusOK,
    check: func(t *testing.T, body []byte) {
    var resp OrderResponse
    if err := json.Unmarshal(body, &resp); err != nil {
        t.Errorf("failed to unmarshal response: %v", err)
    }
    if resp.OrderID == "" {
        t.Error("expected OrderID not to be empty")
    }
    if resp.PastaType != "penne" {
        t.Errorf("expected pasta_type to be 'penne', got '%s'", resp.PastaType)
    }
    if resp.PizzaType != "pepperoni" {
        t.Errorf("expected pizza_type to be 'pepperoni', got '%s'", resp.PizzaType)
    }
    if resp.Price <= 0 {
        t.Error("expected total price to be greater than 0")
    }
    },
    },
    }

    for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
    var reqBody []byte
    var err error
    if s, ok := tt.input.(string); ok {
    reqBody = []byte(s)
    } else {
    reqBody, err = json.Marshal(tt.input)
    if err != nil {
        t.Fatalf("failed to marshal input: %v", err)
    }
    }
    req := httptest.NewRequest("POST", "/order", bytes.NewReader(reqBody))
    w := httptest.NewRecorder()

    CreateOrder(w, req)
    resp := w.Result()
    body, _ := ioutil.ReadAll(resp.Body)

    if resp.StatusCode != tt.expectedStatus {
    t.Errorf("expected status %d, got %d, body: %s", tt.expectedStatus, resp.StatusCode, string(body))
    }
    if tt.expectedStatus != http.StatusOK {
    if string(body) != tt.expectedError+"\n" {
        t.Errorf("expected error message %q, got %q", tt.expectedError, string(body))
    }
    }
    if tt.check != nil {
    tt.check(t, body)
    }
    })
    }
}
// TestResponseContentType verifies that the response Content-Type header is correctly set to application/json
// and that a valid pasta order returns a proper JSON response with a non-empty OrderID.
func TestResponseContentType(t *testing.T) {
    // Prepare a valid pasta-only order request.
    reqBody, err := json.Marshal(map[string]interface{}{"pasta_type": "fettuccine", "weight_grams": 250})
    if err != nil {
        t.Fatalf("failed to marshal request: %v", err)
    }

    req := httptest.NewRequest("POST", "/order", bytes.NewReader(reqBody))
    w := httptest.NewRecorder()

    // Execute the handler.
    CreateOrder(w, req)

    // Check that the response header contains the proper Content-Type.
    contentType := w.Header().Get("Content-Type")
    if contentType != "application/json" {
        t.Errorf("expected Content-Type to be 'application/json', got '%s'", contentType)
    }

    // Verify that the body is valid JSON and contains a non-empty OrderID.
    var resp OrderResponse
    if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
        t.Errorf("failed to unmarshal response: %v", err)
    }
    if resp.OrderID == "" {
        t.Error("expected OrderID not to be empty")
    }
}
// TestExtraFieldsInOrder tests that extra JSON fields are ignored and do not interfere with order processing.
func TestExtraFieldsInOrder(t *testing.T) {
    // Create a valid pasta order with an extra field that should be ignored by the decoder.
    input := map[string]interface{}{
        "pasta_type":  "fettuccine",
        "weight_grams": 350,
        "extra_field":  "ignore me",
    }
    reqBody, err := json.Marshal(input)
    if err != nil {
        t.Fatalf("failed to marshal input: %v", err)
    }
    req := httptest.NewRequest("POST", "/order", bytes.NewReader(reqBody))
    w := httptest.NewRecorder()

    CreateOrder(w, req)
    resp := w.Result()
    if resp.StatusCode != http.StatusOK {
        body, _ := ioutil.ReadAll(resp.Body)
        t.Fatalf("expected status %d, got %d, body: %s", http.StatusOK, resp.StatusCode, string(body))
    }

    var orderResp OrderResponse
    if err := json.Unmarshal(w.Body.Bytes(), &orderResp); err != nil {
        t.Fatalf("failed to unmarshal response: %v", err)
    }

    if orderResp.OrderID == "" {
        t.Error("expected OrderID not to be empty")
    }
    if orderResp.PastaType != "fettuccine" {
        t.Errorf("expected pasta_type to be 'fettuccine', got '%s'", orderResp.PastaType)
    }
}
// TestInvalidPizzaOrder tests that the CreateOrder handler returns an error when an invalid pizza size is provided.
func TestInvalidPizzaOrder(t *testing.T) {
    reqBody, err := json.Marshal(map[string]interface{}{"pizza_type": "margherita", "pizza_size_inch": -1})
    if err != nil {
        t.Fatalf("failed to marshal request: %v", err)
    }
    req := httptest.NewRequest("POST", "/order", bytes.NewReader(reqBody))
    w := httptest.NewRecorder()

    // Execute the order creation, which is expected to fail for invalid pizza size.
    CreateOrder(w, req)

    resp := w.Result()
    body, _ := ioutil.ReadAll(resp.Body)

    if resp.StatusCode != http.StatusBadRequest {
        t.Errorf("expected status %d, got %d, body: %s", http.StatusBadRequest, resp.StatusCode, string(body))
    }

    // Assuming that pizza.NewOrder returns the error message "invalid pizza size" for a negative pizza_size_inch.
    expectedError := "minimum size is 8 inches" + "\n"
    if string(body) != expectedError {
        t.Errorf("expected error message %q, got %q", expectedError, string(body))
    }
}
// TestInvalidPastaOrder verifies that the CreateOrder handler returns an error when an invalid pasta weight is provided.
func TestInvalidPastaOrder(t *testing.T) {
    // Prepare a pasta order with a negative weight, which is invalid.
    reqBody, err := json.Marshal(map[string]interface{}{
        "pasta_type":   "spaghetti",
        "weight_grams": -100,
    })
    if err != nil {
        t.Fatalf("failed to marshal request: %v", err)
    }
    req := httptest.NewRequest("POST", "/order", bytes.NewReader(reqBody))
    w := httptest.NewRecorder()

    // Execute the handler. Expect a BadRequest due to invalid pasta weight.
    CreateOrder(w, req)
    resp := w.Result()
    body, _ := ioutil.ReadAll(resp.Body)

    if resp.StatusCode != http.StatusBadRequest {
        t.Errorf("expected status %d, got %d, body: %s", http.StatusBadRequest, resp.StatusCode, string(body))
    }

    // Expect the error returned by pasta.NewOrder. (Assumed error message)
    expectedError := "minimum order is 100 grams" + "\n"
    if string(body) != expectedError {
        t.Errorf("expected error message %q, got %q", expectedError, string(body))
    }
}
// TestNullPizzaFieldsIgnored verifies that if the JSON payload has null values for pizza fields,
// they are treated as omitted, and the order is processed as a valid pasta-only order.
func TestNullPizzaFieldsIgnored(t *testing.T) {
    // Prepare a valid pasta order with null pizza fields.
    input := `{"pasta_type": "fettuccine", "weight_grams": 200, "pizza_type": null, "pizza_size_inch": null}`
    req := httptest.NewRequest("POST", "/order", bytes.NewReader([]byte(input)))
    w := httptest.NewRecorder()

    // Execute the order creation.
    CreateOrder(w, req)
    resp := w.Result()
    body, _ := ioutil.ReadAll(resp.Body)

    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected status %d, got %d, body: %s", http.StatusOK, resp.StatusCode, string(body))
    }

    var orderResp OrderResponse
    if err := json.Unmarshal(body, &orderResp); err != nil {
        t.Fatalf("failed to unmarshal response: %v", err)
    }

    if orderResp.PastaType != "fettuccine" {
        t.Errorf("expected pasta_type to be 'fettuccine', got '%s'", orderResp.PastaType)
    }

    // Ensure that the pizza-related fields remain empty.
    if orderResp.PizzaType != "" {
        t.Errorf("expected pizza_type to be empty, got '%s'", orderResp.PizzaType)
    }
    if orderResp.PizzaSizeInch != 0 {
        t.Errorf("expected pizza_size_inch to be 0, got %d", orderResp.PizzaSizeInch)
    }

    // Ensure that an OrderID was generated.
    if orderResp.OrderID == "" {
        t.Error("expected OrderID not to be empty")
    }
}
// TestInvalidCombinedOrder tests that if both orders are provided but the pasta order is invalid,
func TestInvalidCombinedOrder(t *testing.T) {
    // Prepare a combined order request with an invalid pasta weight (below the minimum allowed)
    // and valid pizza details.
    reqBody, err := json.Marshal(map[string]interface{}{
        "pasta_type":    "penne",
        "weight_grams":  50,
        "pizza_type":    "margherita",
        "pizza_size_inch": 12,
    })
    if err != nil {
        t.Fatalf("failed to marshal input: %v", err)
    }
    req := httptest.NewRequest("POST", "/order", bytes.NewReader(reqBody))
    w := httptest.NewRecorder()

    // Execute the CreateOrder handler.
    CreateOrder(w, req)

    resp := w.Result()
    body, _ := ioutil.ReadAll(resp.Body)

    // Since the pasta order is invalid, we expect a BadRequest response.
    if resp.StatusCode != http.StatusBadRequest {
        t.Errorf("expected status %d, got %d, body: %s", http.StatusBadRequest, resp.StatusCode, string(body))
    }

    // We assume that pasta.NewOrder returns the error message "minimum order is 100 grams"
    // when the weight is below the allowed minimum.
    expectedError := "minimum order is 100 grams" + "\n"
    if string(body) != expectedError {
        t.Errorf("expected error message %q, got %q", expectedError, string(body))
    }
}