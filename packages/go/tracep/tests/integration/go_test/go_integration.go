package main
import (
	"fmt"
	"github.com/llm-observability/platform/packages/go/tracep"
)
func main() {
	t, err := tracep.New("http://localhost:4318", "test-token-12345", "go-integration-service")
	if err != nil {
		panic(err)
	}
	tid := t.Start("go-live-test")
	t.Trace(tid, "GoClass", "run_test", "step_1", "Hello from Go OTel SDK!")
	t.End(tid, "ok")
	t.Close()
	fmt.Println(tid)
}