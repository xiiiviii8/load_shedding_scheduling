% Fair Rotational Load-Shedding Scheduling
% Decide which areas are switched off in each hour so that supply is respected,
% critical areas are never cut, no area is dark for more than K hours in a row,
% and outages are shared fairly.
include "globals.mzn";

% ---------------- data ----------------
int: nA;                         % number of areas
int: nH;                         % number of hours in the horizon
set of int: A = 1..nA;
set of int: H = 1..nH;
array[A] of 1..3: atype;         % 1 = critical (hospital), 2 = industrial, 3 = residential
array[A] of int: load;           % demand of each area (MW)
array[H] of int: supply;         % available supply in each hour (MW)
int: K = 2;                      % max consecutive hours an area may be off

% ---------------- switches: pass with -D, e.g. -D "fair=true;improved=false" ----------------
bool: fair;                      % true: minimise max outage hours first, then shed load
                                 % false: minimise shed load only (efficiency model)
bool: improved;                  % true: add symmetry breaking + redundant constraints
bool: search;                    % true: use the custom search annotation (CP solvers only)

% ---------------- variables ----------------
array[A, H] of var bool: on;     % on[a,h] = area a has power in hour h

set of int: NC = {a | a in A where atype[a] != 1};     % non-critical areas
int: horizonLoad = sum(load) * nH;

array[A] of var 0..nH: offHours = [sum(h in H)(bool2int(not on[a, h])) | a in A];
var 0..nH: maxOff = max(a in NC)(offHours[a]);
var 0..horizonLoad: shed = sum(a in A, h in H)(load[a] * bool2int(not on[a, h]));

% ---------------- hard constraints ----------------
% C1: critical areas are never switched off
constraint forall(a in A where atype[a] = 1, h in H)(on[a, h]);

% C2: load served in each hour must not exceed the available supply
constraint forall(h in H)(sum(a in A)(load[a] * bool2int(on[a, h])) <= supply[h]);

% C3: no area is off for more than K consecutive hours
%     (every window of K+1 hours contains at least one 'on' hour)
constraint forall(a in NC, h in 1..nH - K)(sum(i in 0..K)(bool2int(on[a, h + i])) >= 1);

% ---------------- model improvements ----------------
% I1 symmetry breaking: areas with the same type and load are interchangeable,
%    so order them by number of outage hours (any solution can be permuted into this order)
array[A] of int: nextTwin = [ min([b | b in a+1..nA where atype[b] = atype[a] /\ load[b] = load[a]] ++ [0]) | a in A ];
constraint if improved then
  forall(a in NC where nextTwin[a] > 0)(offHours[a] >= offHours[nextTwin[a]])
else true endif;

% I2 redundant constraints: in each hour at least minOffCount[h] areas must be off,
%    because even the largest loads must cover the deficit
int: critLoad = sum(a in A where atype[a] = 1)(load[a]);
array[int] of int: sortedNC = reverse(sort([load[a] | a in NC]));
array[H] of int: deficit = [max(0, sum(load) - supply[h]) | h in H];
array[H] of int: minOffCount =
  [ min([k | k in 0..card(NC) where sum(i in 1..k)(sortedNC[i]) >= deficit[h]] ++ [card(NC)]) | h in H ];
constraint if improved then
  forall(h in H)(sum(a in NC)(bool2int(not on[a, h])) >= minOffCount[h])
  /\ maxOff * card(NC) >= sum(minOffCount)
  /\ forall(a in NC)(offHours[a] <= maxOff)
else true endif;

% ---------------- objective ----------------
% fair model: lexicographic (maxOff, shed) encoded as a weighted sum
var int: obj = if fair then maxOff * (horizonLoad + 1) + shed else shed endif;
% S1 search annotation: decide hour by hour, branch on the most constrained area first
%    (dom_w_deg), try 'on' before 'off'; Luby restarts escape bad early choices
ann: custom = seq_search([
  bool_search([on[a, h] | h in H, a in A], dom_w_deg, indomain_max)]);
solve :: if search then custom else seq_search([]) endif
      :: if search then restart_luby(100) else restart_none endif
      minimize obj;

output ["{\"shed\": \(shed), \"maxOff\": \(maxOff), \"obj\": \(obj)}\n"];
