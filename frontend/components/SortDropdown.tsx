import type { SearchSortBy } from "@/lib/types";

const OPTIONS: { value: SearchSortBy; label: string }[] = [
  { value: "relevance", label: "Best match" },
  { value: "distance_asc", label: "Closest" },
  { value: "rating_desc", label: "Top rated" },
  { value: "authenticity_desc", label: "Most authentic" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
];

type Props = {
  value: SearchSortBy;
  onChange: (value: SearchSortBy) => void;
  id?: string;
};

export default function SortDropdown({ value, onChange, id = "sort_by" }: Props) {
  return (
    <select
      id={id}
      value={value}
      onChange={(event) => onChange(event.target.value as SearchSortBy)}
      className="field-select"
    >
      {OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
