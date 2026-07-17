import { Router } from 'express';
import { z } from 'zod';
import { ApiError } from '../../lib/api-error.js';
import { parse, positiveId } from '../../lib/validation.js';

const categories = ['fruit','vegetable','grain','protein','beverage','other'];
const seasons = ['spring','summer','autumn','winter','all'];
export function createFoodsRouter(db) {
 const router=Router();
 router.get('/',(req,res,next)=>{try{const q=parse(z.object({q:z.string().trim().min(1).max(100).optional(),category:z.enum(categories).optional(),season:z.enum(seasons).optional(),page:z.coerce.number().int().min(1).default(1),pageSize:z.coerce.number().int().min(1).max(100).default(20)}).strict(),req.query);const where=[];const values=[];if(q.q){where.push('name LIKE ?');values.push(`%${q.q}%`)}if(q.category){where.push('category = ?');values.push(q.category)}if(q.season){where.push('season = ?');values.push(q.season)}const condition=where.length?`WHERE ${where.join(' AND ')}`:'';const total=db.prepare(`SELECT COUNT(*) AS count FROM food_library ${condition}`).get(...values).count;const rows=db.prepare(`SELECT * FROM food_library ${condition} ORDER BY name, food_id LIMIT ? OFFSET ?`).all(...values,q.pageSize,(q.page-1)*q.pageSize);res.json({data:{items:rows.map(map),page:q.page,pageSize:q.pageSize,total}})}catch(e){next(e)}});
 router.get('/:foodId',(req,res,next)=>{try{const row=db.prepare('SELECT * FROM food_library WHERE food_id = ?').get(parse(positiveId,req.params.foodId));if(!row)throw new ApiError(404,'RESOURCE_NOT_FOUND','Food was not found.');res.json({data:map(row)})}catch(e){next(e)}});return router;
}
function map(r){return{id:r.food_id,name:r.name,calorieKcal:r.calorie_kcal,proteinG:r.protein_g,waterMl:r.water_ml,category:r.category,season:r.season,unitBasis:r.unit_basis,note:r.note}}
