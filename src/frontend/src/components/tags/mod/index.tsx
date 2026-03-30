import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

type DivProps = ComponentPropsWithoutRef<'div'> & Children;
type SpanProps = ComponentPropsWithoutRef<'span'> & Children;
type FormProps = ComponentPropsWithoutRef<'form'> & Children;
type InputProps = ComponentPropsWithoutRef<'input'>;

export const Manager = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-manager", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Hero = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-hero", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Eyebrow = ({ children, className = '', ...rest }: SpanProps) => (
  <span {...rest} className={["mod-eyebrow", className].filter(Boolean).join(' ')}>{children}</span>
);

export const HeroActions = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-hero-actions", className].filter(Boolean).join(' ')}>{children}</div>
);

export const VersionPill = ({ children, className = '', ...rest }: SpanProps) => (
  <span {...rest} className={["mod-version-pill", className].filter(Boolean).join(' ')}>{children}</span>
);

export const Warning = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-warning", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Layout = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-layout", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Column = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-column", className].filter(Boolean).join(' ')}>{children}</div>
);

export const ColumnHeader = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-column-header", className].filter(Boolean).join(' ')}>{children}</div>
);

export const ColumnTools = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-column-tools", className].filter(Boolean).join(' ')}>{children}</div>
);

export const InstalledGrid = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-installed-grid", className].filter(Boolean).join(' ')}>{children}</div>
);

export const InstalledCard = ({ children, missing = false, className = '', ...rest }: any) => {
  const cls = ["mod-installed-card", missing ? "mod-installed-missing" : '', className].filter(Boolean).join(' ');
  return <div {...rest} className={cls}>{children}</div>;
};

export const InstalledHeader = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-installed-header", className].filter(Boolean).join(' ')}>{children}</div>
);

export const InstalledName = ({ children, className = '', ...rest }: SpanProps) => (
  <span {...rest} className={["mod-installed-name", className].filter(Boolean).join(' ')}>{children}</span>
);

export const InstalledVersion = ({ children, className = '', ...rest }: SpanProps) => (
  <span {...rest} className={["mod-installed-version", className].filter(Boolean).join(' ')}>{children}</span>
);

export const InstalledActions = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-installed-actions", className].filter(Boolean).join(' ')}>{children}</div>
);

export const InstalledMeta = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-installed-meta", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Pill = ({ children, className = '', ...rest }: SpanProps) => (
  <span {...rest} className={["mod-pill", className].filter(Boolean).join(' ')}>{children}</span>
);

export const Chip = ({ children, className = '', ...rest }: SpanProps) => (
  <span {...rest} className={["mod-chip", className].filter(Boolean).join(' ')}>{children}</span>
);

export const Placeholder = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-placeholder", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Alert = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-alert", className].filter(Boolean).join(' ')}>{children}</div>
);

export const SearchForm = ({ children, className = '', ...rest }: FormProps) => (
  <form {...rest} className={["mod-search-form", className].filter(Boolean).join(' ')}>{children}</form>
);

export const SearchInput = (props: InputProps) => <input type="search" {...props} />;

export const SearchGrid = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-search-grid", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Card = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-card", className].filter(Boolean).join(' ')}>{children}</div>
);

export const CardThumb = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-card-thumb", className].filter(Boolean).join(' ')}>{children}</div>
);

export const CardThumbEmpty = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-card-thumb-empty", className].filter(Boolean).join(' ')}>{children}</div>
);

export const CardBody = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-card-body", className].filter(Boolean).join(' ')}>{children}</div>
);

export const CardMeta = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-card-meta", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Pagination = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-pagination", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Indicator = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-indicator", className].filter(Boolean).join(' ')}>{children}</div>
);

export const HtmxIndicator = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["htmx-indicator", className].filter(Boolean).join(' ')}>{children}</div>
);

export const DetailPanel = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-detail-panel", className].filter(Boolean).join(' ')}>{children}</div>
);

export const DetailPlaceholder = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-detail-placeholder", className].filter(Boolean).join(' ')}>{children}</div>
);

export const DetailCard = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-detail-card", className].filter(Boolean).join(' ')}>{children}</div>
);

export const DetailThumb = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-detail-thumb", className].filter(Boolean).join(' ')}>{children}</div>
);

export const DetailTags = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-detail-tags", className].filter(Boolean).join(' ')}>{children}</div>
);

export const InstallForm = ({ children, className = '', ...rest }: FormProps) => (
  <form {...rest} className={["mod-install-form", className].filter(Boolean).join(' ')}>{children}</form>
);

export const TokenWarning = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-token-warning", className].filter(Boolean).join(' ')}>{children}</div>
);

export const ReleaseList = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-release-list", className].filter(Boolean).join(' ')}>{children}</div>
);

export const ReleaseRow = ({ children, recommended = false, className = '', ...rest }: any) => (
  <div {...rest} className={["mod-release-row", recommended ? "recommended" : '', className].filter(Boolean).join(' ')}>{children}</div>
);

export const Dependencies = ({ children, className = '', ...rest }: DivProps) => (
  <div {...rest} className={["mod-dependencies", className].filter(Boolean).join(' ')}>{children}</div>
);

export const Toast = ({ children, show = false, className = '', ...rest }: any) => (
  <div {...rest} className={["mod-toast", show ? "show" : '', className].filter(Boolean).join(' ')}>{children}</div>
);

export default {
  Manager,
  Hero,
  Eyebrow,
  HeroActions,
  VersionPill,
  Warning,
  Layout,
  Column,
  ColumnHeader,
  ColumnTools,
  InstalledGrid,
  InstalledCard,
  InstalledHeader,
  InstalledName,
  InstalledVersion,
  InstalledActions,
  InstalledMeta,
  Pill,
  Chip,
  Placeholder,
  Alert,
  SearchForm,
  SearchInput,
  SearchGrid,
  Card,
  CardThumb,
  CardThumbEmpty,
  CardBody,
  CardMeta,
  Pagination,
  Indicator,
  HtmxIndicator,
  DetailPanel,
  DetailPlaceholder,
  DetailCard,
  DetailThumb,
  DetailTags,
  InstallForm,
  TokenWarning,
  ReleaseList,
  ReleaseRow,
  Dependencies,
  Toast,
};
