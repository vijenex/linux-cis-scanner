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
    <title>Amazon Linux 2 CIS Compliance Report - Vijenex</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #c00 0%, #8b0000 100%); color: white; padding: 30px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric { background: white; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s; }
        .metric:hover { transform: translateY(-5px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .metric h3 { font-size: 3em; margin-bottom: 10px; }
        .metric p { font-size: 1.2em; color: #666; text-transform: uppercase; letter-spacing: 1px; }
        .pass h3 { color: #28a745; }
        .fail h3 { color: #dc3545; }
        .manual h3 { color: #ffc107; }
        .results-section { background: white; border-radius: 10px; padding: 30px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .results-section h2 { color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid #c00; }
        .control-item { border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; overflow: hidden; transition: all 0.3s; }
        .control-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .control-header { padding: 15px 20px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; background: #fafafa; transition: background 0.2s; }
        .control-header:hover { background: #f0f0f0; }
        .control-header.active { background: #e8e8e8; }
        .control-info { flex: 1; display: flex; align-items: center; gap: 15px; }
        .control-id { font-weight: bold; color: #c00; min-width: 80px; }
        .control-title { flex: 1; color: #333; }
        .status-badge { padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }
        .status-PASS { background: #d4edda; color: #155724; }
        .status-FAIL { background: #f8d7da; color: #721c24; }
        .status-MANUAL { background: #fff3cd; color: #856404; }
        .status-ERROR { background: #f8d7da; color: #721c24; }
        .status-SKIPPED { background: #e2e3e5; color: #383d41; }
        .expand-icon { font-size: 1.2em; color: #666; transition: transform 0.3s; }
        .expand-icon.rotated { transform: rotate(180deg); }
        .control-details { display: none; padding: 20px; background: white; border-top: 1px solid #e0e0e0; }
        .control-details.show { display: block; animation: slideDown 0.3s ease-out; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .detail-row { margin-bottom: 15px; }
        .detail-label { font-weight: bold; color: #666; margin-bottom: 5px; }
        .detail-value { color: #333; padding: 10px; background: #f8f9fa; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 0.9em; }
        .footer { text-align: center; padding: 30px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Amazon Linux 2 CIS Compliance Report</h1>
        <p>Powered by Vijenex Security Platform</p>
    </div>
    
    <div class="container">
        <div class="summary">
            <div class="metric pass">
                <h3>{{.PassCount}}</h3>
                <p>Passed</p>
            </div>
            <div class="metric fail">
                <h3>{{.FailCount}}</h3>
                <p>Failed</p>
            </div>
            <div class="metric manual">
                <h3>{{.ManualCount}}</h3>
                <p>Manual Review</p>
            </div>
            <div class="metric">
                <h3>{{.TotalCount}}</h3>
                <p>Total Controls</p>
            </div>
        </div>
        
        <div class="results-section">
            <h2>📋 Detailed Compliance Results</h2>
            {{range .Results}}
            <div class="control-item">
                <div class="control-header" onclick="toggleDetails(this)">
                    <div class="control-info">
                        <span class="control-id">{{.ID}}</span>
                        <span class="control-title">{{.Title}}</span>
                    </div>
                    <span class="status-badge status-{{.Status}}">{{.Status}}</span>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="control-details">
                    <div class="detail-row">
                        <div class="detail-label">Section:</div>
                        <div class="detail-value">{{.Section}}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Description:</div>
                        <div class="detail-value">{{.Description}}</div>
                    </div>
                    {{if .CISReference}}
                    <div class="detail-row">
                        <div class="detail-label">CIS Reference:</div>
                        <div class="detail-value">{{.CISReference}}</div>
                    </div>
                    {{end}}
                </div>
            </div>
            {{end}}
        </div>
        
        <div class="footer">
            <p>Generated by Vijenex CIS Scanner for Amazon Linux 2</p>
            <p>https://github.com/vijenex/linux-cis-scanner</p>
        </div>
    </div>
    
    <script>
        function toggleDetails(header) {
            const details = header.nextElementSibling;
            const icon = header.querySelector('.expand-icon');
            
            details.classList.toggle('show');
            icon.classList.toggle('rotated');
            header.classList.toggle('active');
        }
    </script>
</body>
</html>`

type HTMLData struct {
	PassCount   int
	FailCount   int
	ManualCount int
	TotalCount  int
	Results     []Result
}

func GenerateHTML(outputDir string, results []Result) error {
	// Get machine IP
	ip := getMachineIP()
	filename := fmt.Sprintf("vijenex-cis-report-%s.html", ip)
	htmlPath := filepath.Join(outputDir, filename)
	
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
		TotalCount:  len(results),
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
