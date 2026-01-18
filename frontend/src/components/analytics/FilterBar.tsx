"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CalendarIcon, X } from "lucide-react";
import { format } from "date-fns";
import type { AnalyticsFilters, FilterOptions } from "@/lib/api";

interface FilterBarProps {
  filters: AnalyticsFilters;
  filterOptions: FilterOptions | null;
  onChange: (filters: AnalyticsFilters) => void;
}

export function FilterBar({ filters, filterOptions, onChange }: FilterBarProps) {
  const [startDate, setStartDate] = useState<Date | undefined>(
    filters.start_date ? new Date(filters.start_date) : undefined
  );
  const [endDate, setEndDate] = useState<Date | undefined>(
    filters.end_date ? new Date(filters.end_date) : undefined
  );

  const handleStartDateChange = (date: Date | undefined) => {
    setStartDate(date);
    onChange({
      ...filters,
      start_date: date?.toISOString().split("T")[0],
    });
  };

  const handleEndDateChange = (date: Date | undefined) => {
    setEndDate(date);
    onChange({
      ...filters,
      end_date: date?.toISOString().split("T")[0],
    });
  };

  const handleClearFilters = () => {
    setStartDate(undefined);
    setEndDate(undefined);
    onChange({
      trading_mode: filters.trading_mode,
    });
  };

  const hasActiveFilters =
    filters.start_date ||
    filters.end_date ||
    filters.strategy_name ||
    filters.source ||
    filters.status;

  return (
    <div className="flex flex-wrap items-center gap-2 p-4 bg-card rounded-lg border">
      {/* Date Range */}
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="h-8 gap-1">
            <CalendarIcon className="h-3 w-3" />
            {startDate ? format(startDate, "MMM d") : "Start"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={startDate}
            onSelect={handleStartDateChange}
            initialFocus
          />
        </PopoverContent>
      </Popover>

      <span className="text-muted-foreground text-sm">to</span>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="h-8 gap-1">
            <CalendarIcon className="h-3 w-3" />
            {endDate ? format(endDate, "MMM d") : "End"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={endDate}
            onSelect={handleEndDateChange}
            initialFocus
          />
        </PopoverContent>
      </Popover>

      {/* Strategy Filter */}
      <Select
        value={filters.strategy_name || "all"}
        onValueChange={(v) =>
          onChange({ ...filters, strategy_name: v === "all" ? undefined : v })
        }
      >
        <SelectTrigger className="h-8 w-[140px]">
          <SelectValue placeholder="Strategy" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Strategies</SelectItem>
          {filterOptions?.strategies?.map((s) => (
            <SelectItem key={s} value={s}>
              {s}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Source Filter */}
      <Select
        value={filters.source || "all"}
        onValueChange={(v) =>
          onChange({ ...filters, source: v === "all" ? undefined : v })
        }
      >
        <SelectTrigger className="h-8 w-[120px]">
          <SelectValue placeholder="Source" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Sources</SelectItem>
          {filterOptions?.sources?.map((s) => (
            <SelectItem key={s} value={s}>
              {s}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Status Filter */}
      <Select
        value={filters.status || "all"}
        onValueChange={(v) =>
          onChange({ ...filters, status: v === "all" ? undefined : v })
        }
      >
        <SelectTrigger className="h-8 w-[100px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="open">Open</SelectItem>
          <SelectItem value="closed">Closed</SelectItem>
        </SelectContent>
      </Select>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-1 text-muted-foreground"
          onClick={handleClearFilters}
        >
          <X className="h-3 w-3" />
          Clear
        </Button>
      )}
    </div>
  );
}
