# SynqHarbor design system

The visual direction is an editorial midnight harbor: original titanium architecture
above calm water, warm ivory typography, restrained citron and generous spacing.
Manrope handles interface text; Instrument Serif brings an expressive headline voice.
Fonts and media are self-hosted.

The homepage introduces the product and links to substantive product, company,
engineering and policy pages. Shared navigation and the footer provide a complete
site directory. Product pages use diagrammatic compositions; documentation/policies
use readable article layouts and section navigation.

Color and responsive behavior: src/app/globals.css. Public configuration:
src/config/ui.ts. Maintained content and navigation: src/content/. Components
receive content and configuration rather than embedding changeable business copy.

Motion for React provides optional entrance/transitional movement. Content remains
visible before animation runs. Lenis enhances wheel/anchor scrolling while touch
remains native. Reduced motion disables nonessential movement; ambient media can
be paused and pauses when the tab is hidden.

Workspace interactions stay in the current browser tab. The product pages and
technical guides distinguish this available interface from future authenticated
persistence, provider execution and external actions.

Artwork was generated for this project; its silent loop was produced locally using
FFmpeg. No purchased template, customer testimonial or third-party brand portfolio
is used. Free design guidance informed typography, spacing, focus and layout choices.
