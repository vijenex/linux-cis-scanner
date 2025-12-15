package report

import (
	"encoding/csv"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type Result struct {
	ID              string
	Title           string
	Section         string
	Status          string
	CISReference    string
	Remediation     string
	Description     string
}

func GenerateCSV(outputDir string, results []Result) error {
	// Get machine IP
	ip := getMachineIP()
	filename := fmt.Sprintf("vijenex-cis-results-%s.csv", ip)
	csvPath := filepath.Join(outputDir, filename)
	
	file, err := os.Create(csvPath)
	if err != nil {
		return fmt.Errorf("failed to create CSV file: %w", err)
	}
	defer file.Close()
	
	writer := csv.NewWriter(file)
	defer writer.Flush()
	
	// Write header
	header := []string{"Id", "Title", "Section", "Status", "CISReference", "Remediation", "Description"}
	if err := writer.Write(header); err != nil {
		return fmt.Errorf("failed to write CSV header: %w", err)
	}
	
	// Write results
	for _, r := range results {
		row := []string{
			r.ID,
			r.Title,
			r.Section,
			r.Status,
			r.CISReference,
			r.Remediation,
			r.Description,
		}
		if err := writer.Write(row); err != nil {
			return fmt.Errorf("failed to write CSV row: %w", err)
		}
	}
	
	return nil
}

func getMachineIP() string {
	// Try to get primary IP address
	cmd := exec.Command("hostname", "-I")
	output, err := cmd.Output()
	if err == nil {
		ips := strings.Fields(string(output))
		if len(ips) > 0 {
			return ips[0]
		}
	}
	
	// Fallback: try ip command
	cmd = exec.Command("ip", "route", "get", "1")
	output, err = cmd.Output()
	if err == nil {
		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			if strings.Contains(line, "src") {
				fields := strings.Fields(line)
				for i, field := range fields {
					if field == "src" && i+1 < len(fields) {
						return fields[i+1]
					}
				}
			}
		}
	}
	
	// Final fallback: use hostname
	hostname, err := os.Hostname()
	if err == nil {
		return hostname
	}
	
	return "unknown"
}
