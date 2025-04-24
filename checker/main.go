package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"sync"
	"time"
	"net/url"
	"net"
)

const MaxConcurrency = 50

type Config struct {
	URL          string `json:"url"`
	JsonFilePath string `json:"jsonFilePath"`
	Port         int    `json:"port"`
}

type LocationResponse struct {
	Query       string `json:"query"`
	Country     string `json:"country"`
	CountryCode string `json:"countryCode"`
	Region      string `json:"region"`
	RegionName  string `json:"regionName"`
	City        string `json:"city"`
	Status      string `json:"status"`
}

type Output struct {
	URL      string           `json:"url"`
	Location LocationResponse `json:"location"`
}

type InputData struct {
	Configs []Config `json:"configs"`
}

type OutputData struct {
	Outputs []*Output `json:"outputs"`
}

func WaitForPort(port int, timeout time.Duration) error {
	address := fmt.Sprintf("127.0.0.1:%d", port)
	start := time.Now()

	for {
		conn, err := net.DialTimeout("tcp", address, 100*time.Millisecond)
		if err == nil {
			
			conn.Close()
			return nil
		}

		if time.Since(start) > timeout {
			
			return fmt.Errorf("timeout waiting for port %d", port)
		}

		
		time.Sleep(50 * time.Millisecond)
	}
}

func getLocationByPort(proxyPort int) (*LocationResponse, error) {
	proxyURL := fmt.Sprintf("http://127.0.0.1:%d", proxyPort)

	proxy, err := url.Parse(proxyURL)
	if err != nil {
		return nil, fmt.Errorf("error parsing proxy URL: %s", err)
	}

	transport := &http.Transport{
		Proxy: http.ProxyURL(proxy),
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   5 * time.Second,
	}

	url := "http://ip-api.com/json/"

	resp, err := client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var location LocationResponse
	if err := json.Unmarshal(body, &location); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w, body: %s", err, body)
	}

	if location.Status != "success" {
		return nil, fmt.Errorf("location API returned error: %s", location.Status)
	}

	return &location, nil
}


func runXrayCore(jsonFilePath string, xrayCorePath string) *os.Process {
	cmd := exec.Command(xrayCorePath, "-config", jsonFilePath)

	if err := cmd.Start(); err != nil {
		log.Println("Error starting command:", err)
		return nil
	}

	return cmd.Process
}

func checkConfig(xrayCorePath string, jsonFilePath string, port int, url string) (*Output, error) {
	log.Printf("Running XrayCore on port: %v, with the json: %s\n", port, jsonFilePath)

	process := runXrayCore(jsonFilePath, xrayCorePath)
	err := WaitForPort(port, 5 * time.Second)
	if err != nil {
		return nil, fmt.Errorf("failed to wait for port: %s", err)
	}
	
	if process == nil {
		return nil, fmt.Errorf("failed to run XrayCore on port: %v, with the json: %s", port, jsonFilePath)
	}

	location, err := getLocationByPort(port)

	process.Kill()

	if err != nil {
		return nil, err
	}

	output := Output{
		Location: *location,
		URL: url,
	}

	return &output, nil

}

func chunkConfigs(configs []Config, chunkSize int) [][]Config {
	var chunks [][]Config
	for i := 0; i < len(configs); i += chunkSize {
		end := i + chunkSize
		if end > len(configs) {
			end = len(configs)
		}
		chunks = append(chunks, configs[i:end])
	}
	return chunks
}



func handleInputData(input InputData, xrayCorePath string) ([]*Output, error) {
	var allResults []*Output
	chunks := chunkConfigs(input.Configs, 300)

	var wg sync.WaitGroup
	resultChan := make(chan *Output, len(input.Configs))
	semaphore := make(chan struct{}, MaxConcurrency)

	for _, chunk := range chunks {
		for _, config := range chunk {
			wg.Add(1)
			semaphore <- struct{}{}

			go func(config Config) {
				defer wg.Done()
				defer func() { <-semaphore }()

				result, err := checkConfig(xrayCorePath, config.JsonFilePath, config.Port, config.URL)
				if err != nil {
					log.Printf("Error checking the config: %s\n", err)
					return
				}
				log.Printf("Found location %s for config %s", result.Location.Country, result.URL)
				resultChan <- result
			}(config)
		}
	}

	wg.Wait()
	close(resultChan)

	for result := range resultChan {
		allResults = append(allResults, result)
	}

	return allResults, nil
}

//export ProcessProxies
func ProcessProxies(jsonInput *C.char, xrayCorePath *C.char) *C.char {

	// loading the input json by converting it into GoStrings
	// and using json.Unmarshal
	goJsonInput := C.GoString(jsonInput)
	goXrayCorePath := C.GoString(xrayCorePath)
	var input InputData

	err := json.Unmarshal([]byte(goJsonInput), &input)
	if err != nil {
		return C.CString(fmt.Sprintf("Error: Failed to parse json: %v", err))
	}

	output, err := handleInputData(input, goXrayCorePath)

	if err != nil {
		return C.CString(fmt.Sprintf("Error: %v", err))
	}



	jsonBytes, err := json.Marshal(OutputData{
		Outputs: output,
	})
	if err != nil {
		return C.CString(fmt.Sprintf("Error: Error marshaling struct: %v", err))
 	}

	return C.CString(string(jsonBytes))

}

func main() {}