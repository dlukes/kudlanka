/* Compute total number of positions in segs that have been disambiguated at
 * least once.
 *
 * Usage: mongo <dbname> positions_done.js
 */

db.segs.aggregate([
  {$match: {users_size: {$gt: 0}}},
  {$project: {seg_length: {$size: "$utt"}}},
  {$group: {_id: null, sum: {$sum: "$seg_length"}}},
  {$project: {_id: 0, sum: 1}}
]).shellPrint();
