/**
 * TypeScript type definitions for the SQL Dashboard application.
 */

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default: string | null;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
}

export interface RelationshipInfo {
  from_table: string;
  from_columns: string[];
  to_table: string;
  to_columns: string[];
}

export interface DatabaseSchema {
  tables: TableInfo[];
  relationships: RelationshipInfo[];
}

export interface ColumnFilter {
  table: string;
  column: string;
  operator: string;
  value: string | number | boolean;
}

export interface SortConfig {
  column: string;
  direction: 'asc' | 'desc';
}

export interface QueryRequest {
  table: string;
  filters?: ColumnFilter[];
  sort?: SortConfig;
  offset: number;
  limit: number;
}

export interface QueryResponse {
  data: Record<string, any>[];
  total: number;
  offset: number;
  limit: number;
}
