package report

import (
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
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
	csvPath := filepath.Join(outputDir, "vijenex-cis-results.csv")
	
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
