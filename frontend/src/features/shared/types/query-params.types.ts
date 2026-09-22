export type QueryScalar = string | number | boolean;

export type QueryParameterValue = QueryScalar | readonly QueryScalar[] | null | undefined;

export type QueryParameters = Readonly<Record<string, QueryParameterValue>>;
