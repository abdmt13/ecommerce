export interface PaginationParams {
  page: number;
  pageSize: number;
}

export interface PaginationDtoResult<TItem> {
  items: TItem[];
  total: number;
  page: number;
  pageSize: number;
}
