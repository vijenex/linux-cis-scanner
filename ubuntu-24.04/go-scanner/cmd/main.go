package main

import (
	"fmt"
	"os"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"github.com/vijenex/linux-cis-scanner/ubuntu-24.04/internal/scanner"
)

var (
	outputDir  string
	profile    string
	format     string
	milestones []string
)

func main() {
	var rootCmd = &cobra.Command{
		Use:   "vijenex-cis",
		Short: "Vijenex CIS Scanner for Ubuntu 24.04 LTS",
		Long: `
    _    _       _       _        ____    _   _    ____   _   _ 
   | |  | |     | |     | |      |  _ \  | | | |  / __ \ | \ | |
   | |  | |_   _| |__   | |_ ___ | |_) | | | | | | |  | ||  \| |
   | |  | | | | | '_ \  | __/ _ \|  _ <  | | | | | |  | || . ` + "`" + ` |
   | |__| | |_| | |_) | | || (_) | |_) | | |_| | | |__| || |\  |
    \____/ \__,_|_.__/   \__\___/|____/   \___/   \____/ |_| \_|
                                                                
    CIS Security Compliance Scanner
    Ubuntu 24.04 LTS Benchmark
`,
		Run: runScan,
	}

	rootCmd.Flags().StringVar(&outputDir, "output-dir", "./reports", "Output directory for reports")
	rootCmd.Flags().StringVar(&profile, "profile", "Level1", "CIS profile level (Level1 only - Level2 excluded)")
	rootCmd.Flags().StringVar(&format, "format", "both", "Report format (html, csv, both)")
	rootCmd.Flags().StringSliceVar(&milestones, "milestones", []string{}, "Specific milestone files to scan")

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func runScan(cmd *cobra.Command, args []string) {
	cyan := color.New(color.FgCyan, color.Bold)
	green := color.New(color.FgGreen)
	blue := color.New(color.FgBlue)
	yellow := color.New(color.FgYellow)

	// ASCII Art Logo - Ubuntu
	fmt.Println()
	cyan.Println("    _    _       _       _        ____    _   _    ____   _   _ ")
	cyan.Println("   | |  | |     | |     | |      |  _ \\  | | | |  / __ \\ | \\ | |")
	cyan.Println("   | |  | |_   _| |__   | |_ ___ | |_) | | | | | | |  | ||  \\| |")
	cyan.Println("   | |  | | | | | '_ \\  | __/ _ \\|  _ <  | | | | | |  | || . ` |")
	cyan.Println("   | |__| | |_| | |_) | | || (_) | |_) | | |_| | | |__| || |\\  |")
	cyan.Println("    \\____/ \\__,_|_.__/   \\__\\___/|____/   \\___/   \\____/ |_| \\_|")
	fmt.Println()
	cyan.Println("=============================================================")
	cyan.Println("              CIS Security Compliance Scanner                ")
	fmt.Println("           Ubuntu 24.04 LTS Benchmark                       ")
	yellow.Println("           Powered by Vijenex Security Platform             ")
	yellow.Println("           Level 2 Controls Excluded (Level 1 Only)          ")
	cyan.Println("        https://github.com/vijenex/linux-cis-scanner        ")
	cyan.Println("=============================================================")
	fmt.Println()

	// Check if running as root
	if os.Geteuid() != 0 {
		yellow.Println("⚠ Warning: Running without root privileges. Some checks may fail.")
		yellow.Println("  For complete scanning, run with: sudo vijenex-cis")
		fmt.Println()
	}

	blue.Printf("🔍 Starting CIS Compliance Scan...\n")
	blue.Printf("📋 Profile: %s (Level 2 controls excluded)\n", profile)
	blue.Printf("📁 Output: %s\n", outputDir)
	cyan.Println("─────────────────────────────────────────────────────────────")
	fmt.Println()

	startTime := time.Now()

	// Create scanner (always exclude Level 2)
	s := scanner.NewScanner(outputDir, "Level1")

	// Load and execute controls
	if err := s.LoadMilestones(milestones); err != nil {
		color.Red("❌ Error loading milestones: %v", err)
		os.Exit(1)
	}

	results := s.ExecuteControls()

	// Generate reports
	blue.Println("\n📊 Generating reports...")
	if format == "csv" || format == "both" {
		if err := s.GenerateCSVReport(results); err != nil {
			color.Red("❌ Error generating CSV: %v", err)
		} else {
			green.Printf("📊 CSV report: %s/vijenex-cis-results.csv\n", outputDir)
		}
	}

	if format == "html" || format == "both" {
		if err := s.GenerateHTMLReport(results); err != nil {
			color.Red("❌ Error generating HTML: %v", err)
		} else {
			green.Printf("📄 HTML report: %s/vijenex-cis-report.html\n", outputDir)
		}
	}

	duration := time.Since(startTime)

	// Print summary
	fmt.Println()
	cyan.Println("=============================================================")
	cyan.Println("                    SCAN COMPLETED                           ")
	cyan.Println("=============================================================")
	fmt.Printf("Total Checks: %d\n", len(results))
	green.Printf("Passed: %d\n", s.CountStatus(results, "PASS"))
	color.Red("Failed: %d\n", s.CountStatus(results, "FAIL"))
	yellow.Printf("Manual: %d\n", s.CountStatus(results, "MANUAL"))
	yellow.Printf("Not Applicable: %d\n", s.CountStatus(results, "NOT_APPLICABLE"))
	errorCount := s.CountStatus(results, "ERROR")
	if errorCount > 0 {
		color.Red("Errors: %d\n", errorCount)
	}
	fmt.Printf("Duration: %v\n", duration.Round(time.Second))
	cyan.Println("=============================================================")
	fmt.Println()

	green.Println("🎉 Vijenex CIS scan completed successfully!")
}

