"""CSV export and deduplication handler"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, cast
from src.utils import sanitize_filename


class CSVHandler:
    """Handles CSV export and deduplication"""

    def __init__(self, config: dict[str, Any], logger: Any) -> None:
        self.config = config
        self.logger = logger
        self.output_dir = Path(config.get("export", {}).get("output_dir", "data/leads"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_output_directory(self, output_subdir: Optional[str] = None) -> Path:
        """Resolve output directory, optionally scoped to a country subfolder."""
        if not output_subdir:
            return self.output_dir

        subdir_name = sanitize_filename(str(output_subdir).strip())
        if not subdir_name:
            return self.output_dir

        scoped_dir = self.output_dir / subdir_name
        scoped_dir.mkdir(parents=True, exist_ok=True)
        return scoped_dir

    @staticmethod
    def _normalized_text_series(series: Any) -> pd.Series:
        """Normalize text values for stable comparisons and dedup keys."""
        return pd.Series(series).fillna("").astype(str).str.strip().str.lower()

    @classmethod
    def _present_mask(cls, series: Any) -> pd.Series:
        """Return mask for non-empty, meaningful values."""
        normalized = cls._normalized_text_series(series)
        return normalized.ne("") & normalized.ne("nan")

    def export_to_csv(
        self,
        businesses: list[dict[str, Any]],
        search_keyword: str,
        search_city: str,
        output_subdir: Optional[str] = None,
    ) -> Optional[str]:
        """
        Export businesses to CSV file

        Args:
            businesses: List of business dictionaries
            search_keyword: Keyword used for search
            search_city: City searched

        Returns:
            str: Path to exported CSV file or None
        """
        if not businesses:
            self.logger.warning("No businesses to export")
            return None

        # Add metadata to each business
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for business in businesses:
            business["scraped_date"] = timestamp
            business["search_keyword"] = search_keyword
            business["search_city"] = search_city

        # Create DataFrame
        df = pd.DataFrame(businesses)

        # Deduplicate if configured
        if self.config.get("export", {}).get("deduplicate", True):
            original_count = len(df)
            df = self._deduplicate(df)
            new_count = len(df)
            if original_count > new_count:
                self.logger.info(f"Removed {original_count - new_count} duplicate(s)")

        # Reorder columns for better readability
        column_order = [
            "business_name",
            "phone",
            "email",
            "address",
            "city",
            "postal_code",
            "country",
            "website",
            "rating",
            "review_count",
            "category",
            "hours",
            "price_range",
            "google_maps_url",
            "scraped_date",
            "search_keyword",
            "search_city",
        ]

        # Only include columns that exist
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]

        # Generate filename
        sanitized_city = sanitize_filename(search_city)
        sanitized_keyword = sanitize_filename(search_keyword)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitized_city}_{sanitized_keyword}_{date_str}.csv"
        filepath = self._get_output_directory(output_subdir) / filename

        # Export to CSV
        df.to_csv(filepath, index=False, encoding="utf-8")

        self.logger.info(f"✓ Exported {len(df)} businesses to: {filepath}")

        return str(filepath)

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate businesses based on phone number or business name + address

        Args:
            df: DataFrame with business data

        Returns:
            DataFrame with duplicates removed
        """
        working_df = df.copy()

        if "phone" in working_df.columns:
            working_df["_phone_norm"] = self._normalized_text_series(
                working_df["phone"]
            )
        else:
            working_df["_phone_norm"] = ""

        if "business_name" in working_df.columns:
            working_df["_name_norm"] = self._normalized_text_series(
                working_df["business_name"]
            )
        else:
            working_df["_name_norm"] = ""

        if "address" in working_df.columns:
            working_df["_address_norm"] = self._normalized_text_series(
                working_df["address"]
            )
        else:
            working_df["_address_norm"] = ""

        # Strategy 1: deduplicate only when both phone and business name exist.
        # This prevents over-merging different branches sharing one switchboard phone.
        phone_and_name_mask = self._present_mask(
            working_df["_phone_norm"]
        ) & self._present_mask(working_df["_name_norm"])

        if phone_and_name_mask.any():
            phone_name_candidates = cast(pd.DataFrame, working_df[phone_and_name_mask])
            with_phone_and_name = cast(
                pd.DataFrame,
                phone_name_candidates.drop_duplicates(
                    subset=["_phone_norm", "_name_norm"], keep="first"
                ),
            )
            without_phone_and_name = cast(
                pd.DataFrame, working_df[~phone_and_name_mask]
            )
            working_df = cast(
                pd.DataFrame,
                pd.concat(
                    [with_phone_and_name, without_phone_and_name], ignore_index=True
                ),
            )

        # Strategy 2: deduplicate by normalized business name + address,
        # only when both fields are present.
        name_and_address_mask = self._present_mask(
            working_df["_name_norm"]
        ) & self._present_mask(working_df["_address_norm"])

        if name_and_address_mask.any():
            name_address_candidates = cast(
                pd.DataFrame, working_df[name_and_address_mask]
            )
            with_name_and_address = cast(
                pd.DataFrame,
                name_address_candidates.drop_duplicates(
                    subset=["_name_norm", "_address_norm"], keep="first"
                ),
            )
            without_name_and_address = cast(
                pd.DataFrame, working_df[~name_and_address_mask]
            )
            working_df = cast(
                pd.DataFrame,
                pd.concat(
                    [with_name_and_address, without_name_and_address], ignore_index=True
                ),
            )

        return cast(
            pd.DataFrame,
            working_df.drop(columns=["_phone_norm", "_name_norm", "_address_norm"]),
        )

    def merge_csv_files(
        self, csv_files: list[str], output_filename: str = "merged_leads.csv"
    ) -> Optional[str]:
        """
        Merge multiple CSV files and deduplicate

        Args:
            csv_files: List of CSV file paths
            output_filename: Name for merged output file

        Returns:
            str: Path to merged CSV file or None
        """
        if not csv_files:
            self.logger.warning("No CSV files to merge")
            return None

        dfs = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                dfs.append(df)
                self.logger.info(f"Loaded: {csv_file} ({len(df)} rows)")
            except Exception as e:
                self.logger.error(f"Error loading {csv_file}: {e}")

        if not dfs:
            self.logger.warning("No valid CSV files loaded")
            return None

        # Merge all dataframes
        merged_df = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Total rows before deduplication: {len(merged_df)}")

        # Deduplicate
        merged_df = self._deduplicate(merged_df)
        self.logger.info(f"Total rows after deduplication: {len(merged_df)}")

        # Export
        output_path = self.output_dir / output_filename
        merged_df.to_csv(output_path, index=False, encoding="utf-8")

        self.logger.info(f"✓ Merged CSV saved to: {output_path}")

        return str(output_path)

    def get_statistics(self, csv_file: str) -> dict[str, Any]:
        """
        Generate statistics report for a CSV file

        Args:
            csv_file: Path to CSV file

        Returns:
            dict: Statistics dictionary
        """
        try:
            df = pd.read_csv(csv_file)

            def _count_present(column_name: str) -> int:
                if column_name not in df.columns:
                    return 0
                mask = self._present_mask(df[column_name])
                return int(mask.sum())

            stats = {
                "total_businesses": len(df),
                "with_phone": _count_present("phone"),
                "with_email": _count_present("email"),
                "with_website": _count_present("website"),
                "with_rating": df["rating"].notna().sum()
                if "rating" in df.columns
                else 0,
                "unique_cities": df["city"].nunique() if "city" in df.columns else 0,
            }

            # Calculate percentages
            total = stats["total_businesses"]
            if total > 0:
                stats["phone_percentage"] = round(
                    (stats["with_phone"] / total) * 100, 1
                )
                stats["email_percentage"] = round(
                    (stats["with_email"] / total) * 100, 1
                )
                stats["website_percentage"] = round(
                    (stats["with_website"] / total) * 100, 1
                )

            return stats

        except Exception as e:
            self.logger.error(f"Error generating statistics: {e}")
            return {}
