package report

import (
	"fmt"
	"html/template"
	"os"
	"path/filepath"
)

const htmlTemplate = `<!DOCTYPE html>
<html>
<head>
    <title>RHEL 8 CIS Compliance Report - Vijenex</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #c00; color: white; padding: 20px; text-align: center; }
        .summary { display: flex; justify-content: space-around; margin: 20px 0; }
        .metric { text-align: center; padding: 20px; border-radius: 5px; }
        .pass { background: #d4edda; color: #155724; }
        .fail { background: #f8d7da; color: #721c24; }
        .manual { background: #fff3cd; color: #856404; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f2f2f2; }
        .status-pass { color: #28a745; font-weight: bold; }
        .status-fail { color: #dc3545; font-weight: bold; }
        .status-manual { color: #ffc107; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>RHEL 8 CIS Compliance Report</h1>
        <p>Powered by Vijenex Security Platform</p>
    </div>
    
    <div class="summary">
        <div class="metric pass"><h3>{{.PassCount}}</h3><p>Passed</p></div>
        <div class="metric fail"><h3>{{.FailCount}}</h3><p>Failed</p></div>
        <div class="metric manual"><h3>{{.ManualCount}}</h3><p>Manual</p></div>
    </div>
    
    <h3>Detailed Results</h3>
    <table>
        <tr><th>ID</th><th>Control</th><th>Section</th><th>Status</th><th>Details</th></tr>
        {{range .Results}}
        <tr>
            <td>{{.ID}}</td>
            <td>{{.Title}}</td>
            <td>{{.Section}}</td>
            <td class="status-{{.Status | lower}}">{{.Status}}</td>
            <td>{{.Description}}</td>
        </tr>
        {{end}}
    </table>
</body>
</html>`

type HTMLData struct {
	PassCount   int
	FailCount   int
	ManualCount int
	Results     []Result
}

func GenerateHTML(outputDir string, results []Result) error {
	htmlPath := filepath.Join(outputDir, "vijenex-cis-report.html")
	
	// Count statuses
	passCount := 0
	failCount := 0
	manualCount := 0
	for _, r := range results {
		switch r.Status {
		case "PASS":
			passCount++
		case "FAIL":
			failCount++
		case "MANUAL":
			manualCount++
		}
	}
	
	data := HTMLData{
		PassCount:   passCount,
		FailCount:   failCount,
		ManualCount: manualCount,
		Results:     results,
	}
	
	// Create template with custom function
	tmpl := template.Must(template.New("report").Funcs(template.FuncMap{
		"lower": func(s string) string {
			return fmt.Sprintf("%s", s)
		},
	}).Parse(htmlTemplate))
	
	file, err := os.Create(htmlPath)
	if err != nil {
		return fmt.Errorf("failed to create HTML file: %w", err)
	}
	defer file.Close()
	
	if err := tmpl.Execute(file, data); err != nil {
		return fmt.Errorf("failed to execute template: %w", err)
	}
	
	return nil
}
