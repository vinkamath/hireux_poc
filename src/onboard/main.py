import argparse
import logging
from src.onboard.prepare import OnboardPortfolios

def main():
    # Configure argument parser
    parser = argparse.ArgumentParser(
        description='Process portfolio PDFs into structured data.'
    )
    parser.add_argument(
        '--input-dir',
        default='data/input/raw',
        help='Root directory containing portfolio subdirectories (default: data/input/raw)'
    )
    parser.add_argument(
        '--output-dir',
        default='data/output/portfolio',
        help='Directory for processed output (default: data/output/portfolio)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create and run portfolio processor
    try:
        onboarder = OnboardPortfolios(args.input_dir, args.output_dir)
        onboarder.create_structured_portfolios()
    except Exception as e:
        logging.error(f"Portfolio processing failed: {e}")
        raise

if __name__ == "__main__":
    main() 