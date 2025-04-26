package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
)

// Resource struct holds the data for each resource
type Resource struct {
	FilePath   string `json:"filepath"`
	RawResults string `json:"rawResults"`
	Name       string `json:"name"`
}

type Channel struct {
	ChannelID string
	Limit     int
}

var client = &http.Client{}
const V2rayRegex = `(?:vless|vmess|ss|trojan):\/\/[^\n#]+(?:#[^\n]*)?`

func loadAdditionalV2rayURLs(slice *[]string) {
	fmt.Println("Loading additional urls")
	data, err := os.ReadFile("additional_urls.txt")

	if err != nil {
		fmt.Println("Failed to load additional urls:", err)
		return
	}

	*slice = append(*slice, strings.Split(string(data), "\n")...)
}

func parseText(prefix, pattern, text string) []string {

	if data, err := base64.StdEncoding.DecodeString(text); err == nil {
		text = string(data)
	}

    re := regexp.MustCompile(pattern)
    matches := re.FindAllString(text, -1)
    
    // Using a map to remove duplicates
    uniqueProxies := make(map[string]bool)
    for _, proxy := range matches {
        prefixedProxy := prefix + proxy
        uniqueProxies[prefixedProxy] = true
    }

    // Convert the map back to a slice
    result := make([]string, 0, len(uniqueProxies))
    for proxy := range uniqueProxies {
        result = append(result, proxy)
    }

    return result
}

// removePKCS7Padding removes PKCS7 padding from decrypted data
func removePKCS7Padding(data []byte) ([]byte, error) {
	padding := int(data[len(data)-1])
	if padding > len(data) || padding == 0 {
		return nil, fmt.Errorf("invalid padding size")
	}
	for i := 0; i < padding; i++ {
		if data[len(data)-1-i] != byte(padding) {
			return nil, fmt.Errorf("invalid padding byte")
		}
	}
	return data[:len(data)-padding], nil
}

// fetchAndRead fetches content from a URL

func fetchAndRead(url string) (*string, error) {
	client := &http.Client{
		Timeout: 3 * time.Second,
	}

	resp, err := client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	bodyString := string(body)
	return &bodyString, nil
}

func fetchAndDecodeBase64(urls []string) []string {
	var results []string
	for _, url := range urls {
		resp, err := client.Get(url)
		if err != nil {
			log.Println("Error fetching URL:", err)
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == 200 {
			body, err := io.ReadAll(resp.Body)
			if err != nil {
				log.Println("Error reading response body:", err)
				continue
			}
			decoded, err := base64.StdEncoding.DecodeString(string(body))
			if err != nil {
				log.Println("Error decoding Base64:", err)
				continue
			}
			results = append(results, strings.Split(string(decoded), "\n")...)
		}
	}
	return results
}

// fetchAdditionalData fetches and processes MCI, MTN, and Warp data
func fetchAdditionalData(resourceChan chan<- Resource, wg *sync.WaitGroup) {
	defer wg.Done()

	// URLs for MCI and MTN
	mciURLs := []string{
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mci/sub_1.txt",
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mci/sub_2.txt",
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mci/sub_3.txt",
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mci/sub_4.txt",
	}
	mtnURLs := []string{
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mtn/sub_1.txt",
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mtn/sub_2.txt",
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mtn/sub_3.txt",
		"https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/mtn/sub_4.txt",
	}

	// Fetch and decode Base64 data
	mciData := fetchAndDecodeBase64(mciURLs)
	mtnData := fetchAndDecodeBase64(mtnURLs)

	// Fetch Warp data
	warpURL := "https://raw.githubusercontent.com/proSSHvpn/proSSHvpn/main/ProSSH-ALL"
	resp, err := client.Get(warpURL)
	var warpData []string
	if err == nil && resp.StatusCode == 200 {
		body, err := io.ReadAll(resp.Body)
		if err == nil {
			warpData = strings.Split(string(body), "\n")
		}
		resp.Body.Close()
	}

	// Send results to channel
	resourceChan <- Resource{
		FilePath:   "/proxies/v2ray/mci.txt",
		RawResults: strings.Join(mciData, "\n"),
		Name:       "MCI",
	}
	resourceChan <- Resource{
		FilePath:   "/proxies/v2ray/mtn.txt",
		RawResults: strings.Join(mtnData, "\n"),
		Name:       "MTN",
	}
	resourceChan <- Resource{
		FilePath:   "/proxies/v2ray/warp.txt",
		RawResults: strings.Join(warpData, "\n"),
		Name:       "Warp",
	}
}

// fetchAndDecryptMahsa decrypts and processes Mahsa config files
func fetchAndDecryptMahsa(resourceChan chan<- Resource, wg *sync.WaitGroup) {
	defer wg.Done()

	// Define the URL, key, and IV
	url := "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/main/app/sub.txt"
	filePath := "/proxies/v2ray/mahsa-normal.txt"
	key := []byte("ca815ecfdb1f153a")
	iv := []byte("lvcas56410c97lpb")

	// Fetch encrypted data
	resp, err := client.Get(url)
	if err != nil {
		log.Println("Failed to fetch Mahsa configs:", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		log.Println("Failed to fetch Mahsa configs: non-200 status")
		return
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Println("Failed to read response body:", err)
		return
	}

	// Decode the Base64-encoded encrypted data
	encryptedData, err := base64.StdEncoding.DecodeString(string(body))
	if err != nil {
		log.Println("Failed to decode Base64 data:", err)
		return
	}

	// Decrypt the data using AES-CBC
	block, err := aes.NewCipher(key)
	if err != nil {
		log.Println("Failed to create AES cipher:", err)
		return
	}

	if len(encryptedData)%aes.BlockSize != 0 {
		log.Println("Encrypted data is not a multiple of AES block size")
		return
	}

	mode := cipher.NewCBCDecrypter(block, iv)
	decrypted := make([]byte, len(encryptedData))
	mode.CryptBlocks(decrypted, encryptedData)

	// Remove padding
	decrypted, err = removePKCS7Padding(decrypted)
	if err != nil {
		log.Println("Failed to remove PKCS7 padding:", err)
		return
	}

	// Parse decrypted JSON
	var jsonData struct {
		MCI []map[string]string `json:"mci"`
		MTN []map[string]string `json:"mtn"`
	}

	err = json.Unmarshal(decrypted, &jsonData)
	if err != nil {
		log.Println("Failed to parse JSON:", err)
		return
	}

	// Extract URLs from the JSON data
	var urls []string
	for _, item := range append(jsonData.MCI, jsonData.MTN...) {
		if config, ok := item["config"]; ok {
			urls = append(urls, config)
		}
	}

	// Parse URLs using the regex pattern
	pattern := regexp.MustCompile(V2rayRegex)
	parsedResults := pattern.FindAllString(strings.Join(urls, "\n"), -1)

	// Send results to channel
	resourceChan <- Resource{
		FilePath:   filePath,
		RawResults: strings.Join(parsedResults, "\n"),
		Name:       "MahsaNormal",
	}
	log.Println("Mahsa resources processed successfully")
}

func fetchURLsInChunks(urls []string) []string {
	const chunkSize = 300
	var allResults []string

	for i := 0; i < len(urls); i += chunkSize {
		end := i + chunkSize
		if end > len(urls) {
			end = len(urls)
		}
		chunk := urls[i:end]
		results := fetchURLs(chunk)
		allResults = append(allResults, results...)
	}

	return allResults
}

// fetchURLs fetches contents from multiple URLs concurrently
func fetchURLs(urls []string) []string {
	resultChan := make(chan string)
	var wg sync.WaitGroup

	for _, url := range urls {
		wg.Add(1)
		go func(url string) {
			defer wg.Done()
			if result, err := fetchAndRead(url); err == nil {
				resultChan <- *result
			} else {
				log.Println("Error fetching URL:", err)
			}
		}(url)
	}

	go func() {
		wg.Wait()
		close(resultChan)
	}()

	var results []string
	for result := range resultChan {
		results = append(results, result)
	}

	return results
}

// export FetchResources - fetches resources and returns them as a JSON string
//export FetchResources
func FetchResources() *C.char {
	httpResources := []string{
		"https://api.proxyscrape.com/?request=displayproxies&proxytype=http",
		"https://www.proxy-list.download/api/v1/get?type=http",
		"https://www.proxyscan.io/download?type=http",
		"https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
		"https://api.openproxylist.xyz/http.txt",
		"https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt",
		"http://alexa.lr2b.com/proxylist.txt",
		"https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
		"https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
		"https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
		"https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
		"https://proxy-spider.com/api/proxies.example.txt",
		"https://multiproxy.org/txt_all/proxy.txt",
		"https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
		"https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt",
		"https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/https.txt",
		"https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
		"https://openproxylist.xyz/http.txt",
		"https://proxyspace.pro/http.txt",
		"https://proxyspace.pro/https.txt",
		"https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
		"https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
		"https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
		"https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
		"https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
		"https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
		"https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
		"https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
		"https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
		"https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
		"https://raw.githubusercontent.com/RX4096/proxy-list/main/online/https.txt",
		"https://raw.githubusercontent.com/saisuiu/uiu/main/free.txt",
		"https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
		"https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
		"https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
		"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
		"https://rootjazz.com/proxies/proxies.txt",
		"https://sheesh.rip/http.txt",
		"https://www.proxy-list.download/api/v1/get?type=https",
	}
	socks4Resources := []string{
		"https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
		"https://openproxylist.xyz/socks4.txt",
		"https://proxyspace.pro/socks4.txt",
		"https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS4.txt",
		"https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
		"https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
		"https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
		"https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
		"https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
		"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
		"https://www.proxy-list.download/api/v1/get?type=socks4",
		"https://www.proxyscan.io/download?type=socks4",
		"https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all",
		"https://api.openproxylist.xyz/socks4.txt",
	}
	socks5Resources := []string{
		"https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all&simplified=true",
		"https://www.proxy-list.download/api/v1/get?type=socks5",
		"https://www.proxyscan.io/download?type=socks5",
		"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
		"https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
		"https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
		"https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
		"https://api.openproxylist.xyz/socks5.txt",
		"https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
		"https://openproxylist.xyz/socks5.txt",
		"https://proxyspace.pro/socks5.txt",
		"https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
		"https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
		"https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
		"https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
		"https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
	}
	v2rayResources := []string{
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub5.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub6.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub7.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub8.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub9.txt",
		"https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub10.txt",

		"https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet_iOS.txt#(AzadNet.t.me)",
		"https://raw.githubusercontent.com/yebekhe/vpn-fail/main/sub-link",

		"https://raw.githubusercontent.com/mahdibland/SSAggregator/master/sub/sub_merge.txt",
                
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-0",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-1",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-2",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-3",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-4",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-5",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-6",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-7",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-8",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/mixed-9",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/no-match",
		"https://github.com/soroushmirzaei/telegram-configs-collector/blob/main/splitted/subscribe",
		
	}


	// loadAdditionalV2rayURLs(&v2rayResources)

	var allResources []Resource
	var wg sync.WaitGroup
	resourceChan := make(chan Resource)

	// fetch resources and send them to channel
	fetchAndSend := func(urls []string, name, filePath string, regexPattern string, prefix string) {
		defer wg.Done()
		contents := fetchURLsInChunks(urls)
		parsedTexts := parseText(prefix, regexPattern, strings.Join(contents, "\n"))


		resourceChan <- Resource{
			FilePath:   filePath,
			RawResults: strings.Join(parsedTexts, "\n"),
			Name:       name,
		}
	}

	wg.Add(4)
	go fetchAndSend(
		httpResources, 
		"Http", 
		"/proxies/regular/http.txt", 
		`\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b`,
		"http://", 
	)
	go fetchAndSend(
		socks4Resources, 
		"Socks4", 
		"/proxies/regular/socks4.txt", 
		`\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b`,
		"socks4://", 
	)
	go fetchAndSend(
		socks5Resources, 
		"Socks5", 
		"/proxies/regular/socks5.txt", 
		`\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b`,
		"socks5://", 
	)
	go fetchAndSend(
		v2rayResources, 
		"V2ray", 
		"/proxies/v2ray/mixed.txt", 
		V2rayRegex, 
		"",
	)
	
	// For additional data!
	wg.Add(2)
	go fetchAdditionalData(resourceChan, &wg)
	go fetchAndDecryptMahsa(resourceChan, &wg)

	// Wait for all goroutines to finish
	go func() {
		wg.Wait()
		close(resourceChan)
	}()

	// Collect results from channel
	for resource := range resourceChan {
		allResources = append(allResources, resource)
	}

	// Convert to JSON
	jsonData, err := json.Marshal(allResources)
	if err != nil {
		return C.CString("{}") // Return empty JSON if error occurs
	}

	// Return JSON as C string
	return C.CString(string(jsonData))
}


func fetchTGMessages(channelID string, requested int) []string {
	var messages []string
	var before string

	channel := "https://t.me/s/" + channelID
	req, err := http.NewRequest("GET", channel, nil)
	if err != nil {
		log.Printf("Error when requesting to: %s Error : %s", channel, err)
		return messages
	}

	resp, err := client.Do(req)
	if err != nil {
		log.Print(err)
		return messages
	}
	defer resp.Body.Close()

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		log.Print(err)
		return messages
	}

	messageChan := make(chan string, 200)

	doc.Find(".tgme_widget_message_text").Each(func(i int, s *goquery.Selection) {
		if msg := extractFormattedText(s); msg != "" {
			messageChan <- msg
		}
	})

	before = doc.Find(".tme_messages_more").AttrOr("data-before", "")

	count := (requested / 20) + 1
	var wg sync.WaitGroup

	for i := 0; i < count && before != ""; i++ {
		wg.Add(1)
		go func(beforeVal string) {
			defer wg.Done()

			nextPageURL := fmt.Sprintf("https://t.me/s/%s?before=%s", channelID, beforeVal)
			req, err := http.NewRequest("GET", nextPageURL, nil)
			if err != nil {
				log.Print(err)
				return
			}

			resp, err := client.Do(req)
			if err != nil {
				log.Print(err)
				return
			}
			defer resp.Body.Close()

			doc, err := goquery.NewDocumentFromReader(resp.Body)
			if err != nil {
				log.Print(err)
				return
			}

			doc.Find(".tgme_widget_message_text").Each(func(i int, s *goquery.Selection) {
				if msg := extractFormattedText(s); msg != "" {
					messageChan <- msg
				}
			})
		}(before)
	}

	go func() {
		wg.Wait()
		close(messageChan)
	}()

	for msg := range messageChan {
		messages = append(messages, msg)
	}

	if len(messages) > requested {
		messages = messages[:requested]
	}

	return messages
}

func extractFormattedText(s *goquery.Selection) string {
	html, err := s.Html()
	if err != nil {
		log.Print(err)
		return ""
	}

	html = strings.ReplaceAll(html, "<br>", "\n")
	html = strings.ReplaceAll(html, "<br/>", "\n")
	html = strings.ReplaceAll(html, "<br />", "\n")
	html = strings.ReplaceAll(html, "</p>", "\n")
	html = strings.ReplaceAll(html, "<p>", "")

	text := stripHTML(html)
	return strings.TrimSpace(text)
}

func stripHTML(input string) string {
	re := regexp.MustCompile(`<.*?>`)
	return re.ReplaceAllString(input, "")
}

//export FetchTGChannels
func FetchTGChannels(data *C.char) *C.char {
	resourcesChan := make(chan Resource, 100)
	goData := C.GoString(data)

	var wg sync.WaitGroup

	fetchAndSend := func(channelID string, amount int, filepath string) {
		defer wg.Done()
		tgMessages := fetchTGMessages(channelID, amount)

		rawContents := strings.Join(tgMessages, "\n")

		resourcesChan <- Resource{
			FilePath:  filepath,
			RawResults: rawContents,
			Name:      channelID,
		}
	}

	var rawData map[string]struct {
		Limit int `json:"limit"`
	}

	err := json.Unmarshal([]byte(goData), &rawData)
	if err != nil {
		log.Fatalf("Failed to read json: %v", err)
	}

	for channelID, data := range rawData {
		wg.Add(1)
		go fetchAndSend(
			channelID,
			data.Limit,
			fmt.Sprintf("/proxies/tvc/%s.txt", channelID),
		)
	}

	go func() {
		wg.Wait()
		close(resourcesChan)
	}()

	var allResources []Resource
	for resource := range resourcesChan {
		allResources = append(allResources, resource)
	}

	jsonData, err := json.Marshal(allResources)
	if err != nil {
		return C.CString("{}") // Return empty JSON if error occurs
	}

	return C.CString(string(jsonData))
}

func main() {}
