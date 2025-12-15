package main

import (
	"fmt"
	"os"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"github.com/vijenex/linux-cis-scanner/rhel-9/internal/scanner"
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
		Short: "Vijenex CIS Scanner for RHEL 9",
		Long: `
██████╗ ██╗  ██╗███████╗██╗          █████╗ 
██╔══██╗██║  ██║██╔════╝██║         ██╔══██╗
██████╔╝███████║█████╗  ██║         ╚█████╔╝
██╔══██╗██╔══██║██╔══╝  ██║          ╚═══██╗
██║  ██║██║  ██║███████╗███████╗    █████╔╝ 
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚════╝  

    Vijenex CIS Scanner
    Red Hat Enterprise Linux 9
    Security Compliance Automation
`,
		Run: runScan,
	}

	rootCmd.Flags().StringVar(&outputDir, "output-dir", "./reports", "Output directory for reports")
	rootCmd.Flags().StringVar(&profile, "profile", "Level1", "CIS profile level (Level1, Level2)")
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

	fmt.Println()
	cyan.Println("██████╗ ██╗  ██╗███████╗██╗          █████╗ ")
	cyan.Println("██╔══██╗██║  ██║██╔════╝██║         ██╔══██╗")
	cyan.Println("██████╔╝███████║█████╗  ██║         ╚█████╔╝")
	cyan.Println("██╔══██╗██╔══██║██╔══╝  ██║          ╚═══██╗")
	cyan.Println("██║  ██║██║  ██║███████╗███████╗    █████╔╝ ")
	cyan.Println("╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚════╝  ")
	fmt.Println()
	cyan.Println("=============================================================")
	cyan.Println("                        VIJENEX                              ")
	fmt.Println("      Red Hat Enterprise Linux 9 CIS Scanner           ")
	yellow.Println("           Powered by Vijenex Security Platform             ")
	cyan.Println("        https://github.com/vijenex/linux-cis-scanner        ")
	cyan.Println("=============================================================")
	fmt.Println()

	if os.Geteuid() != 0 {
		yellow.Println("⚠ Warning: Running without root privileges. Some checks may fail.")
		yellow.Println("  For complete scanning, run with: sudo vijenex-cis")
		fmt.Println()
	}

	blue.Printf("🔍 Starting CIS Compliance Scan...\n")
	blue.Printf("📋 Profile: %s\n", profile)
	blue.Printf("📁 Output: %s\n", outputDir)
	cyan.Println("─────────────────────────────────────────────────────────────")
	fmt.Println()

	startTime := time.Now()

	s := scanner.NewScanner(outputDir, profile)

	if err := s.LoadMilestones(milestones); err != nil {
		color.Red("❌ Error loading milestones: %v", err)
		os.Exit(1)
	}

	results := s.ExecuteControls()

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

	fmt.Println()
	cyan.Println("=============================================================")
	cyan.Println("                    SCAN COMPLETED                           ")
	cyan.Println("=============================================================")
	fmt.Printf("Total Checks: %d\n", len(results))
	green.Printf("Passed: %d\n", s.CountStatus(results, "PASS"))
	color.Red("Failed: %d\n", s.CountStatus(results, "FAIL"))
	yellow.Printf("Manual: %d\n", s.CountStatus(results, "MANUAL"))
	fmt.Printf("Duration: %v\n", duration.Round(time.Second))
	cyan.Println("=============================================================")
	fmt.Println()

	green.Println("🎉 Vijenex CIS scan completed successfully!")
}
