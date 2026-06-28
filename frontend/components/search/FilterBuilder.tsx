import React from "react";
import { MetadataFilter } from "../../lib/types/models";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Plus, X } from "lucide-react";

export function FilterBuilder({ filters, onChange }: { filters: MetadataFilter[]; onChange: (f: MetadataFilter[]) => void }) {
  const addFilter = () => {
    onChange([...filters, { field: "", operator: "==", value: "" }]);
  };

  const removeFilter = (index: number) => {
    const newFilters = [...filters];
    newFilters.splice(index, 1);
    onChange(newFilters);
  };

  const updateFilter = (index: number, key: keyof MetadataFilter, val: string) => {
    const newFilters = [...filters];
    newFilters[index] = { ...newFilters[index], [key]: val };
    onChange(newFilters);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-foreground">Filters</h4>
        <Button type="button" variant="ghost" size="sm" onClick={addFilter} className="h-7 px-2 text-xs">
          <Plus className="mr-1 h-3 w-3" /> Add Filter
        </Button>
      </div>
      {filters.length === 0 ? (
        <p className="text-xs text-muted-foreground">No filters applied.</p>
      ) : (
        <div className="space-y-2">
          {filters.map((filter, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <Input
                placeholder="Field (e.g. year)"
                value={filter.field}
                onChange={(e) => updateFilter(idx, "field", e.target.value)}
                className="h-8"
              />
              <select
                className="flex h-8 w-24 items-center justify-between rounded-md border border-input bg-background px-2 py-1 text-xs shadow-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                value={filter.operator}
                onChange={(e) => updateFilter(idx, "operator", e.target.value)}
              >
                <option value="==">==</option>
                <option value="!=">!=</option>
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
                <option value="in">in</option>
              </select>
              <Input
                placeholder="Value"
                value={filter.value}
                onChange={(e) => updateFilter(idx, "value", e.target.value)}
                className="h-8"
              />
              <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => removeFilter(idx)}>
                <X className="h-4 w-4" />
                <span className="sr-only">Remove filter</span>
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
