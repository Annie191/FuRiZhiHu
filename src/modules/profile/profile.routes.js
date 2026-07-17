import { Router } from 'express';
import { parseProfilePatch } from './profile.schema.js';
export function createProfileRouter(service) { const router = Router(); router.get('/', (req,res,next)=>{try{res.json({data:service.get(req.auth.userId)});}catch(e){next(e);}}); router.patch('/',(req,res,next)=>{try{res.json({data:service.update(req.auth.userId,parseProfilePatch(req.body))});}catch(e){next(e);}}); return router; }
