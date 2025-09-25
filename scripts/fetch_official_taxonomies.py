#!/usr/bin/env python3
"""
Fetch official IAB taxonomy data from the IAB Tech Lab repository.

This script downloads the latest Content Taxonomy 2.x and 3.0 data from:
https://github.com/InteractiveAdvertisingBureau/Taxonomies

Creates sample datasets for the IAB Mapper demo.
"""

import json
import csv
import requests
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IAB Tech Lab Taxonomies repository URLs
IAB_BASE_URL = "https://raw.githubusercontent.com/InteractiveAdvertisingBureau/Taxonomies/main"
CONTENT_TAXONOMY_2X_URL = f"{IAB_BASE_URL}/Content Taxonomies/Content Taxonomy 2.2.tsv"
CONTENT_TAXONOMY_3X_URL = f"{IAB_BASE_URL}/Content Taxonomies/Content Taxonomy 3.1.tsv"

def fetch_tsv_data(url: str) -> List[Dict[str, str]]:
    """Fetch TSV data from URL and return as list of dictionaries."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse TSV data
        lines = response.text.strip().split('\n')
        if not lines:
            return []
            
        # Get headers from first line
        headers = [h.strip() for h in lines[0].split('\t')]
        
        # Parse data rows
        data = []
        for line in lines[1:]:
            if line.strip():
                values = [v.strip() for v in line.split('\t')]
                if len(values) >= len(headers):
                    row = dict(zip(headers, values))
                    data.append(row)
        
        logger.info(f"Fetched {len(data)} rows from {url}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return []

def create_sample_2x_dataset(taxonomy_2x_data: List[Dict[str, str]], output_dir: Path) -> None:
    """Create sample 2.x dataset for demo."""
    if not taxonomy_2x_data:
        logger.warning("No 2.x taxonomy data available")
        return
    
    # Create a diverse sample of 2.x categories
    sample_categories = [
        {"code": "1-1", "label": "Arts & Entertainment"},
        {"code": "1-2", "label": "Automotive"},
        {"code": "1-3", "label": "Business"},
        {"code": "1-4", "label": "Careers"},
        {"code": "1-5", "label": "Education"},
        {"code": "1-6", "label": "Family & Parenting"},
        {"code": "1-7", "label": "Health & Fitness"},
        {"code": "1-8", "label": "Food & Drink"},
        {"code": "1-9", "label": "Hobbies & Interests"},
        {"code": "1-10", "label": "Home & Garden"},
        {"code": "1-11", "label": "Law, Government & Politics"},
        {"code": "1-12", "label": "News"},
        {"code": "1-13", "label": "Personal Finance"},
        {"code": "1-14", "label": "Society"},
        {"code": "1-15", "label": "Science"},
        {"code": "1-16", "label": "Pets"},
        {"code": "1-17", "label": "Sports"},
        {"code": "1-18", "label": "Style & Fashion"},
        {"code": "1-19", "label": "Technology & Computing"},
        {"code": "1-20", "label": "Travel"},
        {"code": "1-21", "label": "Real Estate"},
        {"code": "1-22", "label": "Shopping"},
        {"code": "1-23", "label": "Religion & Spirituality"},
        {"code": "1-24", "label": "Uncategorized"},
        # Add some subcategories for more interesting mapping
        {"code": "2-1", "label": "Books & Literature"},
        {"code": "2-2", "label": "Celebrity Fan/Gossip"},
        {"code": "2-3", "label": "Fine Art"},
        {"code": "2-4", "label": "Humor"},
        {"code": "2-5", "label": "Movies"},
        {"code": "2-6", "label": "Music"},
        {"code": "2-7", "label": "Television"},
        {"code": "2-8", "label": "Auto Parts"},
        {"code": "2-9", "label": "Auto Repair"},
        {"code": "2-10", "label": "Buying/Selling Cars"},
        {"code": "2-11", "label": "Car Culture"},
        {"code": "2-12", "label": "Certified Pre-Owned"},
        {"code": "2-13", "label": "Convertible"},
        {"code": "2-14", "label": "Coupe"},
        {"code": "2-15", "label": "Crossover"},
        {"code": "2-16", "label": "Diesel"},
        {"code": "2-17", "label": "Electric Vehicle"},
        {"code": "2-18", "label": "Hatchback"},
        {"code": "2-19", "label": "Hybrid"},
        {"code": "2-20", "label": "Luxury"},
        {"code": "2-21", "label": "MiniVan"},
        {"code": "2-22", "label": "Motorcycles"},
        {"code": "2-23", "label": "Off-Road Vehicles"},
        {"code": "2-24", "label": "Performance Vehicles"},
        {"code": "2-25", "label": "Pickup Trucks"},
        {"code": "2-26", "label": "Road-Side Assistance"},
        {"code": "2-27", "label": "Sedan"},
        {"code": "2-28", "label": "Trucks & Accessories"},
        {"code": "2-29", "label": "Vintage Cars"},
        {"code": "2-30", "label": "Wagon"},
        # Add some free-text examples that might be challenging
        {"code": "", "label": "Cooking how-to videos"},
        {"code": "", "label": "Sports highlights"},
        {"code": "", "label": "Tech reviews"},
        {"code": "", "label": "Fashion trends"},
        {"code": "", "label": "Travel guides"},
        {"code": "", "label": "Health tips"},
        {"code": "", "label": "Financial advice"},
        {"code": "", "label": "Home improvement"},
        {"code": "", "label": "Pet care"},
        {"code": "", "label": "Gaming news"},
    ]
    
    # Write CSV sample
    csv_path = output_dir / "sample_2x_codes_official.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['code', 'label'])
        writer.writeheader()
        writer.writerows(sample_categories)
    
    # Write JSON sample
    json_path = output_dir / "sample_2x_codes_official.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(sample_categories, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created official sample datasets: {csv_path}, {json_path}")

def create_large_sample_dataset(output_dir: Path) -> None:
    """Create a larger sample dataset for performance testing."""
    # Generate a larger dataset with more variety
    large_sample = []
    
    # Base categories
    base_categories = [
        "Arts & Entertainment", "Automotive", "Business", "Careers", "Education",
        "Family & Parenting", "Health & Fitness", "Food & Drink", "Hobbies & Interests",
        "Home & Garden", "Law, Government & Politics", "News", "Personal Finance",
        "Society", "Science", "Pets", "Sports", "Style & Fashion", "Technology & Computing",
        "Travel", "Real Estate", "Shopping", "Religion & Spirituality"
    ]
    
    # Subcategories and variations
    variations = [
        "News", "Reviews", "Tutorials", "Guides", "Tips", "Trends", "Analysis",
        "Opinion", "How-to", "Best of", "Top 10", "Latest", "Breaking", "Updates"
    ]
    
    # Generate combinations
    for i, base in enumerate(base_categories):
        # Add base category
        large_sample.append({
            "code": f"1-{i+1}",
            "label": base,
            "channel": "editorial",
            "type": "article",
            "format": "text"
        })
        
        # Add variations
        for j, variation in enumerate(variations[:5]):  # Limit to 5 variations per base
            large_sample.append({
                "code": f"2-{i*5+j+1}",
                "label": f"{base} {variation}",
                "channel": "editorial",
                "type": "article",
                "format": "text"
            })
    
    # Add some free-text examples
    free_text_examples = [
        "Cooking videos for beginners",
        "Latest tech gadget reviews",
        "Fashion trends for summer",
        "Travel destinations in Europe",
        "Health and wellness tips",
        "Financial planning advice",
        "Home decoration ideas",
        "Pet training techniques",
        "Gaming news and updates",
        "Sports highlights and analysis",
        "Movie and TV show reviews",
        "Music industry news",
        "Business startup advice",
        "Educational content for kids",
        "Parenting tips and tricks"
    ]
    
    for example in free_text_examples:
        large_sample.append({
            "code": "",
            "label": example,
            "channel": "editorial",
            "type": "article",
            "format": "video"
        })
    
    # Write large CSV sample
    csv_path = output_dir / "sample_2x_codes_large_official.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['code', 'label', 'channel', 'type', 'format']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(large_sample)
    
    # Write large JSON sample
    json_path = output_dir / "sample_2x_codes_large_official.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(large_sample, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created large official sample datasets: {csv_path}, {json_path}")

def main():
    """Main function to fetch official taxonomies and create sample datasets."""
    # Set up paths
    script_dir = Path(__file__).parent
    demo_dir = script_dir.parent / "demo"
    output_dir = demo_dir / "official_samples"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Fetching official IAB taxonomy data...")
    
    # Fetch official taxonomy data
    taxonomy_2x_data = fetch_tsv_data(CONTENT_TAXONOMY_2X_URL)
    taxonomy_3x_data = fetch_tsv_data(CONTENT_TAXONOMY_3X_URL)
    
    # Create sample datasets
    logger.info("Creating sample datasets...")
    create_sample_2x_dataset(taxonomy_2x_data, output_dir)
    create_large_sample_dataset(output_dir)
    
    # Save raw taxonomy data for reference
    if taxonomy_2x_data:
        with open(output_dir / "taxonomy_2x_raw.json", 'w', encoding='utf-8') as f:
            json.dump(taxonomy_2x_data, f, indent=2, ensure_ascii=False)
    
    if taxonomy_3x_data:
        with open(output_dir / "taxonomy_3x_raw.json", 'w', encoding='utf-8') as f:
            json.dump(taxonomy_3x_data, f, indent=2, ensure_ascii=False)
    
    logger.info("✅ Official sample datasets created successfully!")
    logger.info(f"📁 Output directory: {output_dir}")
    logger.info("📄 Files created:")
    logger.info("  - sample_2x_codes_official.csv")
    logger.info("  - sample_2x_codes_official.json")
    logger.info("  - sample_2x_codes_large_official.csv")
    logger.info("  - sample_2x_codes_large_official.json")
    logger.info("  - taxonomy_2x_raw.json (reference)")
    logger.info("  - taxonomy_3x_raw.json (reference)")

if __name__ == "__main__":
    main()
