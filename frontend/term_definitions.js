/**
 * AeroX Global Information Tooltip System
 * ─────────────────────────────────────────
 * Usage:  Add  data-tooltip="TERM_KEY"  to ANY element.
 *         The tooltip engine auto-attaches on DOMContentLoaded.
 *         For dynamically-rendered cards call:  window.initTooltips(container)
 *
 * Keys are UPPER_SNAKE_CASE. New terms → just add to AEROX_TERMS below.
 */

// ═══════════════════════════════════════════════════════════════════════════
// 1. TERM DICTIONARY
// ═══════════════════════════════════════════════════════════════════════════
window.AEROX_TERMS = {

  // ── Fare Components ──────────────────────────────────────────────────────
  BASE_FARE: {
    title: 'Base Fare',
    body:  'The core ticket price set by the airline before any taxes, airport charges, or additional fees are added. It is the starting point of your total ticket cost.'
  },
  FUEL_SURCHARGE: {
    title: 'Fuel Surcharge (YQ)',
    body:  'An extra charge airlines levy to recover rising aviation fuel (ATF) costs. It fluctuates with global crude oil prices and can vary significantly between carriers and routes.'
  },
  TAXES_FEES: {
    title: 'Taxes & Airport Fees',
    body:  'Mandatory government-levied charges including Passenger Service Fee (PSF), User Development Fee (UDF), and other airport-specific levies. These are non-negotiable and passed directly to authorities.'
  },
  TOTAL_FARE: {
    title: 'Total Fare',
    body:  'The all-inclusive ticket price — Base Fare + Fuel Surcharge + Taxes & Fees. This is the final amount you pay at checkout.'
  },
  FARE_BREAKDOWN: {
    title: 'Fare Breakdown',
    body:  'A detailed split of every cost component that makes up your total ticket price, helping you understand where each rupee goes.'
  },

  // ── Pricing Intelligence ─────────────────────────────────────────────────
  APIX: {
    title: 'APIx — Airline Pricing Intelligence Index',
    body:  "AeroX's composite index that measures how an airline's current fare compares to historical norms for the same route and travel window. A high APIx signals premium pricing; a low APIx signals a deal."
  },
  FARE_SHOCK: {
    title: 'Fare Shock',
    body:  'A sudden and significant spike in ticket prices — usually triggered by surge demand, seat scarcity, or external events. AeroX flags Fare Shock when fares deviate sharply from the 30-day route average.'
  },
  PRICE_TREND: {
    title: 'Price Trend',
    body:  'The directional movement of fares over time (rising, falling, or stable) for a specific route. AeroX uses historical data to project whether prices are likely to go up or down.'
  },
  FAIR_PRICE: {
    title: 'Fair Price',
    body:  "AeroX's computed benchmark of what a ticket on this route should cost based on historical averages, seasonality, and competitor pricing."
  },
  PRICE_ALERT: {
    title: 'Price Alert',
    body:  "A notification triggered when a tracked flight's fare crosses a user-defined threshold — either drops below a target or rises above a limit."
  },
  ROUTE_BASKET: {
    title: 'Route Basket',
    body:  'A curated set of comparable routes used as a pricing benchmark. AeroX compares your selected route against routes in the basket to detect whether fares are unusually high or low.'
  },
  CPI: {
    title: 'CPI — Comparative Price Index',
    body:  'A metric that compares the current fare of a flight against the average market fare across all airlines and platforms for the same origin-destination pair and travel date.'
  },
  DEMAND_SIGNAL: {
    title: 'Demand Signal',
    body:  "AeroX's real-time indicator of seat demand on a route. High demand signals usually precede fare increases, while low demand may present booking opportunities."
  },
  LEAD_TIME: {
    title: 'Lead Time',
    body:  'The number of days between today and your travel date. Research shows that fares on most Indian domestic routes are lowest when booked 30–45 days in advance.'
  },
  BOOKING_WINDOW: {
    title: 'Booking Window',
    body:  'The time period during which buying a ticket tends to offer the best value. AeroX highlights the optimal booking window for each route based on historical fare patterns.'
  },

  // ── Regulatory & Industry Bodies ─────────────────────────────────────────
  DGCA: {
    title: 'DGCA — Directorate General of Civil Aviation',
    body:  "India's apex civil aviation regulatory authority. The DGCA oversees airline licensing, safety standards, fare caps during emergencies, and passenger rights enforcement."
  },
  MOCA: {
    title: 'MoCA — Ministry of Civil Aviation',
    body:  'The Indian government ministry that sets national aviation policy, approves new routes, and oversees schemes like UDAN (regional connectivity).'
  },
  UDAN: {
    title: 'UDAN — Ude Desh Ka Aam Naagrik',
    body:  "India's regional connectivity scheme that subsidises flights to smaller towns and tier-2/3 cities, making air travel affordable and accessible to the common citizen."
  },
  IATA: {
    title: 'IATA — International Air Transport Association',
    body:  'The global trade body for airlines. IATA sets standards for ticketing, safety, and baggage. IATA codes (e.g., DEL, BOM) uniquely identify airports worldwide.'
  },
  ATF: {
    title: 'ATF — Aviation Turbine Fuel',
    body:  'The specialised kerosene-based fuel used by commercial jet aircraft. ATF prices, set monthly by oil companies in India, directly affect airline operating costs and ticket prices.'
  },

  // ── Platforms & Distribution ──────────────────────────────────────────────
  OTA: {
    title: 'OTA — Online Travel Agency',
    body:  'Third-party digital platforms (e.g., MakeMyTrip, Goibibo, Ixigo, Cleartrip, Yatra, EaseMyTrip) that aggregate and sell airline tickets, often offering additional deals or cashback.'
  },
  GDS: {
    title: 'GDS — Global Distribution System',
    body:  'Technology platforms (e.g., Amadeus, Sabre, Galileo) that act as intermediaries between airlines and travel agencies, distributing seat inventory and fare data in real time.'
  },
  API: {
    title: 'API — Application Programming Interface',
    body:  'A standardised data connection that allows AeroX to securely fetch live flight prices, availability, and schedules from airlines and OTAs in real time.'
  },

  // ── Flight & Route Identifiers ────────────────────────────────────────────
  IATA_CODE: {
    title: 'IATA Airport Code',
    body:  'A unique 3-letter code assigned by IATA to identify each airport globally (e.g., DEL = Delhi, BOM = Mumbai). AeroX uses these codes for route searches and fare comparisons.'
  },
  FLIGHT_NUMBER: {
    title: 'Flight Number',
    body:  "A unique alphanumeric code (e.g., 6E 204) assigned to a scheduled flight service. The letters denote the airline's IATA code and the digits identify the specific flight."
  },
  CABIN_CLASS: {
    title: 'Cabin Class',
    body:  'The seating tier on a flight — Economy, Premium Economy, Business, or First Class. Each class offers different seat pitch, baggage allowance, meals, and price points.'
  },
  FARE_CLASS: {
    title: 'Fare Class / Booking Class',
    body:  'An inventory bucket (e.g., Y, B, M, Q) within a cabin that determines the price, refund rules, and upgrade eligibility for a specific seat. Airlines manage multiple fare classes per flight.'
  },
  SEAT_AVAILABILITY: {
    title: 'Seat Availability',
    body:  'The number of seats remaining in a specific fare class on a flight. As seats fill up, airlines move passengers to pricier fare buckets, causing fares to rise.'
  },

  // ── Baggage ───────────────────────────────────────────────────────────────
  CABIN_BAGGAGE: {
    title: 'Cabin Baggage',
    body:  'Hand luggage you carry into the aircraft cabin. DGCA mandates a minimum of 7 kg for domestic flights. Some fare classes or airlines may offer more.'
  },
  CHECKED_BAGGAGE: {
    title: 'Checked Baggage',
    body:  'Luggage stored in the aircraft hold and checked in at the airport counter. Allowances vary by airline and fare class; excess baggage incurs additional charges.'
  },

  // ── Market & Analytics ────────────────────────────────────────────────────
  MARKET_SHARE: {
    title: 'Market Share',
    body:  'The percentage of total passengers or flights operated by a specific airline on a route or market. Dominant airlines often have more pricing power on their stronghold routes.'
  },
  LOAD_FACTOR: {
    title: 'Load Factor',
    body:  'The percentage of available seats filled by paying passengers. Higher load factors indicate strong demand and typically lead to higher fares.'
  },
  YIELD: {
    title: 'Yield (Revenue per Passenger Km)',
    body:  'A key airline profitability metric — the average revenue earned per passenger per kilometre flown. AeroX uses yield trends to explain pricing behaviour on a route.'
  },
  RPK: {
    title: 'RPK — Revenue Passenger Kilometres',
    body:  'Total kilometres flown by all revenue-paying passengers. A standard global measure of airline traffic volume used to compare growth across carriers and periods.'
  },
  ASK: {
    title: 'ASK — Available Seat Kilometres',
    body:  "Total kilometres flown multiplied by the number of available seats. Represents an airline's total capacity offered in a period. Higher ASK with lower RPK signals under-demand."
  },

  // ── AeroX-Specific Features ───────────────────────────────────────────────
  LIVE_FARES: {
    title: 'Live Fares',
    body:  'Real-time ticket prices fetched directly from airline systems and OTAs at the moment of your search. Prices may change every few minutes due to dynamic pricing algorithms.'
  },
  HISTORICAL_FARES: {
    title: 'Historical Fares',
    body:  'A record of past ticket prices for a route over time. AeroX uses this data to build benchmarks, detect anomalies, and help you identify whether today\'s price is a deal or not.'
  },
  ANOMALY_DETECTION: {
    title: 'Anomaly Detection',
    body:  "AeroX's AI-powered engine that automatically identifies unusual pricing patterns — such as sudden spikes, unexpected dips, or fare inconsistencies across platforms."
  },
  KPI: {
    title: 'KPI — Key Performance Indicator',
    body:  "A measurable value that tracks performance. In AeroX's context, KPIs include metrics like average fare, price deviation, load factor, and route popularity."
  },
  SURGE_PRICING: {
    title: 'Surge Pricing',
    body:  'Dynamic fare escalation triggered by high demand or low seat availability. Airlines use real-time algorithms to maximise revenue — AeroX monitors and flags surge events.'
  },
  DYNAMIC_PRICING: {
    title: 'Dynamic Pricing',
    body:  'A revenue management strategy where airlines continuously adjust ticket prices based on demand, competition, time to departure, and remaining seat inventory.'
  },
  PSF: {
    title: 'PSF — Passenger Service Fee',
    body:  'A statutory fee collected by airports and passed to the Airport Authority of India (AAI) to fund terminal services and infrastructure. Included in every domestic ticket.'
  },
  UDF: {
    title: 'UDF — User Development Fee',
    body:  'An airport-specific levy charged at select airports (e.g., Delhi, Mumbai, Hyderabad, Bangalore) to fund new terminal development and infrastructure projects.'
  },
  GST: {
    title: 'GST — Goods and Services Tax',
    body:  "India's unified indirect tax. Air tickets attract 5% GST on Economy class fares and 12% GST on Business class fares. GST is included in the total fare displayed."
  },
  CONVENIENCE_FEE: {
    title: 'Convenience Fee',
    body:  'A non-refundable service charge added by Online Travel Agencies (OTAs) like MakeMyTrip, Ixigo, or Cleartrip for processing your booking. Direct airline bookings typically waive this fee entirely.'
  },
  PSD: {
    title: 'PSD — Passenger Seat Demand',
    body:  "DGCA's official traffic distribution metric that measures passenger demand across India's 462 domestic corridors. AeroX uses PSD data to assign route weights in the National Basket Index."
  },

  // ── Regulatory & Industry Bodies ─────────────────────────────────────────
  MOSPI: {
    title: 'MoSPI — Ministry of Statistics and Programme Implementation',
    body:  "India's central statistical authority responsible for compiling official economic data including the Consumer Price Index (CPI), GDP, and industrial production indices. Official CPI is published monthly with a ~12-day lag."
  },
  NSO: {
    title: 'NSO — National Statistical Office',
    body:  'The apex body under MoSPI responsible for compiling and publishing official national-level statistics including CPI, IIP, and national accounts data.'
  },
  RBI: {
    title: 'RBI — Reserve Bank of India',
    body:  "India's central bank and monetary authority. RBI monitors inflation (including airfare contributions to CPI) and sets repo rates that influence the broader economy."
  },
  AERA: {
    title: 'AERA — Airports Economic Regulatory Authority',
    body:  'Statutory tariff regulator established under the AERA Act, 2008. AERA approves aeronautical charges (UDF, PSF) at major Indian airports to ensure fair pricing.'
  },
  UDAN: {
    title: 'UDAN — Ude Desh Ka Aam Naagrik',
    body:  "India's regional connectivity scheme that subsidises flights to smaller towns and tier-2/3 cities, making air travel affordable and accessible to the common citizen."
  },
  IATA: {
    title: 'IATA — International Air Transport Association',
    body:  'The global trade body for airlines. IATA sets standards for ticketing, safety, and baggage. IATA codes (e.g., DEL, BOM) uniquely identify airports worldwide.'
  },
  ATF: {
    title: 'ATF — Aviation Turbine Fuel',
    body:  'The specialised kerosene-based fuel used by commercial jet aircraft. ATF prices, set monthly by oil marketing companies in India, directly affect airline operating costs and ticket prices.'
  },
  OMC: {
    title: 'OMC — Oil Marketing Company',
    body:  'Public sector oil corporations (Indian Oil, BPCL, HPCL) that supply jet fuel (ATF) and establish domestic benchmark prices updated bi-monthly.'
  },
  AOG: {
    title: 'AOG — Aircraft on Ground',
    body:  'A technical grounding event where an aircraft is unfit to fly due to mechanical issues. AOG events reduce fleet capacity, causing sudden supply shocks and fare spikes on affected routes.'
  },

  // ── Market & Analytics ────────────────────────────────────────────────────
  MARKET_SHARE: {
    title: 'Market Share',
    body:  'The percentage of total passengers or flights operated by a specific airline on a route or market. Dominant airlines often have more pricing power on their stronghold routes.'
  },
  LOAD_FACTOR: {
    title: 'Load Factor',
    body:  'The percentage of available seats filled by paying passengers. Higher load factors indicate strong demand and typically lead to higher fares as fewer cheap seats remain.'
  },
  YIELD: {
    title: 'Yield (Revenue per Passenger Km)',
    body:  'A key airline profitability metric — the average revenue earned per passenger per kilometre flown. AeroX uses yield trends to explain pricing behaviour on a route.'
  },
  RPK: {
    title: 'RPK — Revenue Passenger Kilometres',
    body:  'Total kilometres flown by all revenue-paying passengers. A standard global measure of airline traffic volume used to compare growth across carriers and periods.'
  },
  ASK: {
    title: 'ASK — Available Seat Kilometres',
    body:  "Total kilometres flown multiplied by the number of available seats. Represents an airline's total capacity offered in a period. Higher ASK with lower RPK signals under-demand."
  },
  VOLATILITY: {
    title: 'Price Volatility (CV%)',
    body:  'The statistical coefficient of variation — how much fares fluctuate around the average on a given route. High volatility (>20%) means prices are unpredictable; low volatility means stable pricing.'
  },
  DOD: {
    title: 'DoD — Day-over-Day Change',
    body:  'The percentage change in a metric (e.g., APIx or average fare) compared to the previous day. Useful for tracking rapid short-term price movements.'
  },
  WOW: {
    title: 'WoW — Week-over-Week Change',
    body:  'The percentage change in a metric compared to the same day last week. Helps identify weekly seasonal trends such as weekend pricing patterns.'
  },
  YOY: {
    title: 'YoY — Year-over-Year Change',
    body:  'The percentage change in a metric compared to the same period in the previous year. A standard benchmark for evaluating long-term growth or inflation.'
  },

  // ── Statistical Methods ───────────────────────────────────────────────────
  JEVONS: {
    title: 'Jevons Geometric Mean Index',
    body:  'A price index formula that computes the geometric (not arithmetic) average of price relatives. Used by AeroX and international statistical bodies (ILO, IMF) to eliminate upward substitution bias in price indices.'
  },
  LASPEYRES: {
    title: 'Laspeyres Index (Upper-Level Weighting)',
    body:  'A weighted price index that uses fixed base-period quantities (e.g., DGCA passenger traffic weights) to aggregate elementary route indices into a national headline figure.'
  },
  IQR_FILTER: {
    title: 'IQR Filter — Interquartile Range Outlier Removal',
    body:  'A statistical technique that removes extreme fare outliers (e.g., obvious data errors or ghost prices) by discarding values outside 1.5× the interquartile range. Ensures clean index calculations.'
  },
  BASKET_WEIGHT: {
    title: 'Basket Weight',
    body:  "The proportional contribution of a specific route to the overall National Airfare Index, based on its share of DGCA-recorded passenger traffic. Higher-traffic routes carry more weight in the index."
  },
  ANOMALY: {
    title: 'Anomaly / Anomaly Detection',
    body:  "AeroX's statistical engine that automatically flags unusual fare behaviour — such as 3-sigma deviations, sudden spikes, unexpected drops, or cross-platform price inconsistencies."
  },
  ANOMALY_DETECTION: {
    title: 'Anomaly Detection',
    body:  "AeroX's AI-powered engine that automatically identifies unusual pricing patterns — such as sudden spikes, unexpected dips, or fare inconsistencies across platforms."
  },
  PERCENTILE: {
    title: 'Percentile (Pxx)',
    body:  'A statistical measure that indicates the percentage of observations below a given value. P10 = cheapest 10% of fares; P90 = most expensive 10% of fares observed on the route.'
  },
  MA: {
    title: 'Moving Average (MA)',
    body:  'A smoothed trend line calculated by averaging values over a rolling time window (e.g., 7-day or 30-day). Reduces day-to-day noise to reveal the underlying price direction.'
  },
  STRESS_SCORE: {
    title: 'Fare Stress Score',
    body:  'AeroX composite indicator (0–100) measuring the intensity of price pressure across the national airspace basket. Scores >70 indicate elevated market stress requiring monitoring.'
  },

  // ── AeroX-Specific Concepts ───────────────────────────────────────────────
  INDEX: {
    title: 'Price Index',
    body:  'A normalised number that represents how the current price level compares to a chosen base period (AeroX uses 2024 = 100). An index of 150 means prices are 50% higher than the 2024 baseline.'
  },
  INFLATION: {
    title: 'Inflation',
    body:  'The rate at which general price levels rise over time. Airfare inflation refers specifically to how aviation ticket prices are trending upward. High airfare inflation contributes to the broader CPI Transport sub-group.'
  },
  SCRAPED_RATE: {
    title: 'Real-Time Scraped Rate',
    body:  "A fare collected from a live online source (airline website or OTA) by AeroX's automated Playwright scraper, rather than a manually entered or estimated value."
  },
  REF_FARE: {
    title: 'Reference Fare',
    body:  'A comparison fare used by AeroX as a pricing benchmark for a given route, date, and lead-time horizon. Derived from historical averages. Current fares are measured relative to this reference.'
  },
  LIVE_FARES: {
    title: 'Live / Real-Time Scraped Fare',
    body:  "Ticket prices fetched live from airline systems and OTAs at the moment of search. Collected by AeroX's Playwright-based scraping engine and cleaned before display. Prices may change every few minutes."
  },
  DYNAMIC_PRICING: {
    title: 'Dynamic Pricing',
    body:  'A revenue management strategy where airlines continuously adjust ticket prices based on demand, competition, time to departure, and remaining seat inventory.'
  },
  SURGE_PRICING: {
    title: 'Surge Pricing',
    body:  'Dynamic fare escalation triggered by high demand or low seat availability. Airlines use real-time algorithms to maximise revenue — AeroX monitors and flags surge events on all major corridors.'
  },
  PRICE_PRESSURE: {
    title: 'Price Pressure',
    body:  'AeroX indicator showing the intensity of upward or downward airfare movement on a route or across the national basket. High pressure = fares are rising rapidly above baseline.'
  }
};



// ═══════════════════════════════════════════════════════════════════════════
// 2. SELF-CONTAINED CSS INJECTION
// ═══════════════════════════════════════════════════════════════════════════
(function injectTooltipCSS() {
  if (document.getElementById('aerox-tooltip-css')) return;
  var s = document.createElement('style');
  s.id = 'aerox-tooltip-css';
  s.textContent = [
    /* Anchor term styling */
    '.agt-term {',
    '  display: inline;',
    '  cursor: help;',
    '  border-bottom: 1.5px dashed rgba(96,165,250,0.7);',
    '  padding-bottom: 1px;',
    '  transition: border-color 0.2s;',
    '}',
    '.agt-term:hover {',
    '  border-bottom-color: #60a5fa;',
    '}',
    /* Tooltip bubble */
    '#aerox-global-tooltip {',
    '  position: fixed;',
    '  z-index: 99999;',
    '  max-width: 300px;',
    '  min-width: 200px;',
    '  pointer-events: none;',
    '  opacity: 0;',
    '  transition: opacity 0.18s ease;',
    '  font-family: "Inter", "SF Pro Display", system-ui, sans-serif;',
    '}',
    '#aerox-global-tooltip.agt-visible {',
    '  pointer-events: none;',
    '}',
    '.agt-inner {',
    '  background: rgba(15,23,42,0.97);',
    '  border: 1px solid rgba(96,165,250,0.25);',
    '  border-radius: 10px;',
    '  padding: 11px 14px 12px;',
    '  box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 2px 8px rgba(96,165,250,0.08);',
    '  backdrop-filter: blur(12px);',
    '  -webkit-backdrop-filter: blur(12px);',
    '}',
    '.agt-title {',
    '  font-size: 12px;',
    '  font-weight: 700;',
    '  color: #93c5fd;',
    '  letter-spacing: 0.02em;',
    '  margin-bottom: 5px;',
    '  line-height: 1.3;',
    '}',
    '.agt-body {',
    '  font-size: 11.5px;',
    '  color: rgba(226,232,240,0.88);',
    '  line-height: 1.55;',
    '  font-weight: 400;',
    '}',
    /* Compact (title-only) variant */
    '#aerox-global-tooltip.agt-compact .agt-inner {',
    '  padding: 6px 11px 7px;',
    '}',
    '#aerox-global-tooltip.agt-compact .agt-title {',
    '  font-size: 11.5px;',
    '  margin-bottom: 0;',
    '  color: #e2e8f0;',
    '}',
    /* Compact anchor — no dashed underline, just cursor */
    '.agt-term-compact {',
    '  border-bottom: none !important;',
    '  cursor: help;',
    '}'
  ].join('\n');
  (document.head || document.documentElement).appendChild(s);
}());

// ═══════════════════════════════════════════════════════════════════════════
// 3. TOOLTIP DOM ENGINE
// ═══════════════════════════════════════════════════════════════════════════
(function () {
  'use strict';

  // ── Create the single shared tooltip element ──────────────────────────────
  let tooltipEl = null;

  function ensureTooltip() {
    if (tooltipEl) return tooltipEl;
    tooltipEl = document.createElement('div');
    tooltipEl.id = 'aerox-global-tooltip';
    tooltipEl.setAttribute('role', 'tooltip');
    tooltipEl.innerHTML =
      '<div class="agt-inner">' +
        '<div class="agt-title"></div>' +
        '<div class="agt-body"></div>' +
      '</div>';
    document.body.appendChild(tooltipEl);
    return tooltipEl;
  }

  // ── Position the tooltip smartly within the viewport ─────────────────────
  function positionTooltip(anchorEl) {
    var tip    = ensureTooltip();
    var rect   = anchorEl.getBoundingClientRect();
    var tw     = tip.offsetWidth  || 280;
    var th     = tip.offsetHeight || 80;
    var vw     = window.innerWidth;
    var vh     = window.innerHeight;
    var OFFSET = 10;

    // Default: place above the anchor (fixed coords — no scrollY needed)
    var top  = rect.top - th - OFFSET;
    var left = rect.left + rect.width / 2 - tw / 2;

    // Flip below if not enough room above
    if (top < 8) {
      top = rect.bottom + OFFSET;
    }

    // Clamp vertically (in case screen is tiny)
    if (top + th > vh - 8) top = vh - th - 8;

    // Clamp horizontally
    if (left < 8)           left = 8;
    if (left + tw > vw - 8) left = vw - tw - 8;

    tip.style.top  = top  + 'px';
    tip.style.left = left + 'px';
  }

  // ── Show tooltip ──────────────────────────────────────────────────────────
  function showTooltip(anchorEl, termKey, compact) {
    var def = window.AEROX_TERMS[termKey];
    if (!def) return;

    var tip = ensureTooltip();
    tip.querySelector('.agt-title').textContent = def.title;

    var bodyEl = tip.querySelector('.agt-body');
    if (compact) {
      bodyEl.textContent = '';
      bodyEl.style.display = 'none';
      tip.classList.add('agt-compact');
    } else {
      bodyEl.textContent  = def.body;
      bodyEl.style.display = '';
      tip.classList.remove('agt-compact');
    }

    tip.style.top     = '0px';
    tip.style.left    = '0px';
    tip.style.opacity = '0';
    tip.classList.add('agt-visible');

    requestAnimationFrame(function () {
      positionTooltip(anchorEl);
      tip.style.opacity = '1';
    });
  }

  // ── Hide tooltip ──────────────────────────────────────────────────────────
  function hideTooltip() {
    if (!tooltipEl) return;
    tooltipEl.style.opacity = '0';
    tooltipEl.classList.remove('agt-visible');
  }

  // ── Attach listeners to a single element ─────────────────────────────────
  function attachTooltipToElement(el) {
    if (el._agtBound) return;
    el._agtBound = true;

    var key     = el.getAttribute('data-tooltip');
    var compact = el.hasAttribute('data-tooltip-compact');
    if (!key || !window.AEROX_TERMS[key]) return;

    el.classList.add('agt-term');
    if (compact) el.classList.add('agt-term-compact');

    el.addEventListener('mouseenter', function () { showTooltip(el, key, compact); });
    el.addEventListener('mouseleave', hideTooltip);
    el.addEventListener('focusin',    function () { showTooltip(el, key, compact); });
    el.addEventListener('focusout',   hideTooltip);
    el.addEventListener('click', function (e) {
      if (tooltipEl && tooltipEl.classList.contains('agt-visible')) {
        hideTooltip();
      } else {
        e.stopPropagation();
        showTooltip(el, key, compact);
      }
    });
  }

  // ── Public: scan a container (or document) for tooltip anchors ───────────
  window.initTooltips = function (root) {
    var scope = root || document;
    scope.querySelectorAll('[data-tooltip]').forEach(attachTooltipToElement);
  };

  // ── Close tooltip on outside click ───────────────────────────────────────
  document.addEventListener('click', hideTooltip);

  // ── Auto-init on DOM ready ────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { window.initTooltips(); });
  } else {
    window.initTooltips();
  }

  // ── Re-scan after dynamic content (MutationObserver) ─────────────────────
  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (!m.addedNodes.length) return;
      m.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        if (node.hasAttribute && node.hasAttribute('data-tooltip')) {
          attachTooltipToElement(node);
        }
        if (node.querySelectorAll) {
          node.querySelectorAll('[data-tooltip]').forEach(attachTooltipToElement);
        }
      });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });

}());
