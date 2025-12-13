# app/repositories/api_call_log_repository.py
"""
API调用日志Repository
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from app.models.api_call_log import ApiCallLog
from app.repositories.base import BaseRepository


class ApiCallLogRepository(BaseRepository[ApiCallLog]):
    """API调用日志Repository"""
    
    def __init__(self, db: Session):
        super().__init__(ApiCallLog, db)
    
    def create_api_call(
        self,
        user_id: int,
        model_id: int,
        endpoint: str,
        request_tokens: int = 0,
        response_tokens: int = 0,
        response_time_ms: Optional[int] = None,
        status_code: Optional[int] = None,
        is_success: bool = True,
        error_message: Optional[str] = None,
        conversation_id: Optional[int] = None
    ) -> ApiCallLog:
        """
        创建API调用日志
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            endpoint: 调用端点
            request_tokens: 请求token数
            response_tokens: 响应token数
            response_time_ms: 响应时间（毫秒）
            status_code: 状态码
            is_success: 是否成功
            error_message: 错误信息
            conversation_id: 对话ID
            
        Returns:
            API调用日志实例
        """
        total_tokens = request_tokens + response_tokens
        
        log_data = {
            "user_id": user_id,
            "model_id": model_id,
            "conversation_id": conversation_id,
            "endpoint": endpoint,
            "request_tokens": request_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "is_success": is_success,
            "error_message": error_message
        }
        
        return self.create(log_data)
    
    def get_user_api_calls(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_id: Optional[int] = None,
        is_success: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ApiCallLog]:
        """
        获取用户的API调用记录
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            model_id: 模型ID
            is_success: 是否成功
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            API调用记录列表
        """
        query = self.db.query(ApiCallLog).filter(
            ApiCallLog.user_id == user_id
        )
        
        if start_date:
            query = query.filter(ApiCallLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(ApiCallLog.created_at <= end_date)
        
        if model_id:
            query = query.filter(ApiCallLog.model_id == model_id)
        
        if is_success is not None:
            query = query.filter(ApiCallLog.is_success == is_success)
        
        query = query.order_by(ApiCallLog.created_at.desc())
        
        return query.offset(skip).limit(limit).all()
    
    def get_model_api_calls(
        self,
        model_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_success: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ApiCallLog]:
        """
        获取模型的API调用记录
        
        Args:
            model_id: 模型ID
            start_date: 开始日期
            end_date: 结束日期
            is_success: 是否成功
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            API调用记录列表
        """
        query = self.db.query(ApiCallLog).filter(
            ApiCallLog.model_id == model_id
        )
        
        if start_date:
            query = query.filter(ApiCallLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(ApiCallLog.created_at <= end_date)
        
        if is_success is not None:
            query = query.filter(ApiCallLog.is_success == is_success)
        
        query = query.order_by(ApiCallLog.created_at.desc())
        
        return query.offset(skip).limit(limit).all()
    
    # def get_api_usage_stats(
    #     self,
    #     user_id: Optional[int] = None,
    #     model_id: Optional[int] = None,
    #     start_date: Optional[datetime] = None,
    #     end_date: Optional[datetime] = None
    # ) -> Dict[str, Any]:
    #     """
    #     获取API使用统计
        
    #     Args:
    #         user_id: 用户ID（可选）
    #         model_id: 模型ID（可选）
    #         start_date: 开始日期
    #         end_date: 结束日期
            
    #     Returns:
    #         统计信息字典
    #     """
    #     query = self.db.query(
    #         func.count(ApiCallLog.log_id).label('total_calls'),
    #         func.sum(ApiCallLog.request_tokens).label('total_request_tokens'),
    #         func.sum(ApiCallLog.response_tokens).label('total_response_tokens'),
    #         func.sum(ApiCallLog.total_tokens).label('total_tokens'),
    #         func.avg(ApiCallLog.response_time_ms).label('avg_response_time'),
    #         func.avg(
    #             func.case((ApiCallLog.is_success == True, 1), else_=0)
    #         ).label('success_rate')
    #     )
        
    #     if user_id:
    #         query = query.filter(ApiCallLog.user_id == user_id)
        
    #     if model_id:
    #         query = query.filter(ApiCallLog.model_id == model_id)
        
    #     if start_date:
    #         query = query.filter(ApiCallLog.created_at >= start_date)
        
    #     if end_date:
    #         query = query.filter(ApiCallLog.created_at <= end_date)
        
    #     result = query.first()
        
    #     return {
    #         "total_calls": result[0] or 0,
    #         "total_request_tokens": result[1] or 0,
    #         "total_response_tokens": result[2] or 0,
    #         "total_tokens": result[3] or 0,
    #         "avg_response_time": float(result[4] or 0),
    #         "success_rate": float(result[5] or 0)
    #     }
    
    
    def get_api_usage_stats(
        self,
        user_id: Optional[int] = None,
        model_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取API使用统计
        
        Args:
            user_id: 用户ID（可选）
            model_id: 模型ID（可选）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        from sqlalchemy import case
        
        # 使用case函数
        success_case = case(
            (ApiCallLog.is_success == True, 1),
            else_=0
        )
        
        query = self.db.query(
            func.count(ApiCallLog.log_id).label('total_calls'),
            func.sum(ApiCallLog.request_tokens).label('total_request_tokens'),
            func.sum(ApiCallLog.response_tokens).label('total_response_tokens'),
            func.sum(ApiCallLog.total_tokens).label('total_tokens'),
            func.avg(ApiCallLog.response_time_ms).label('avg_response_time'),
            func.avg(success_case).label('success_rate')
        )
        
        if user_id:
            query = query.filter(ApiCallLog.user_id == user_id)
        
        if model_id:
            query = query.filter(ApiCallLog.model_id == model_id)
        
        if start_date:
            query = query.filter(ApiCallLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(ApiCallLog.created_at <= end_date)
        
        result = query.first()
        
        return {
            "total_calls": result[0] or 0,
            "total_request_tokens": result[1] or 0,
            "total_response_tokens": result[2] or 0,
            "total_tokens": result[3] or 0,
            "avg_response_time": float(result[4] or 0),
            "success_rate": float(result[5] or 0)
        }

    
    
    # def get_daily_usage_stats(
    #     self,
    #     days: int = 30,
    #     user_id: Optional[int] = None,
    #     model_id: Optional[int] = None
    # ) -> List[Dict[str, Any]]:
    #     """
    #     获取每日使用统计
        
    #     Args:
    #         days: 统计天数
    #         user_id: 用户ID（可选）
    #         model_id: 模型ID（可选）
            
    #     Returns:
    #         每日统计列表
    #     """
    #     end_date = datetime.now()
    #     start_date = end_date - timedelta(days=days)
        
    #     query = self.db.query(
    #         func.date(ApiCallLog.created_at).label('date'),
    #         func.count(ApiCallLog.log_id).label('call_count'),
    #         func.sum(ApiCallLog.total_tokens).label('total_tokens'),
    #         func.avg(
    #             func.case((ApiCallLog.is_success == True, 1), else_=0)
    #         ).label('success_rate')
    #     ).filter(
    #         ApiCallLog.created_at >= start_date,
    #         ApiCallLog.created_at <= end_date
    #     )
        
    #     if user_id:
    #         query = query.filter(ApiCallLog.user_id == user_id)
        
    #     if model_id:
    #         query = query.filter(ApiCallLog.model_id == model_id)
        
    #     query = query.group_by(
    #         func.date(ApiCallLog.created_at)
    #     ).order_by(
    #         func.date(ApiCallLog.created_at).desc()
    #     )
        
    #     results = query.all()
        
    #     return [
    #         {
    #             "date": date.strftime('%Y-%m-%d'),
    #             "call_count": call_count,
    #             "total_tokens": total_tokens or 0,
    #             "success_rate": float(success_rate or 0)
    #         }
    #         for date, call_count, total_tokens, success_rate in results
    #     ]

    def get_daily_usage_stats(
        self,
        days: int = 30,
        user_id: Optional[int] = None,
        model_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取每日使用统计
        
        Args:
            days: 统计天数
            user_id: 用户ID（可选）
            model_id: 模型ID（可选）
            
        Returns:
            每日统计列表
        """
        from sqlalchemy import case
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        success_case = case(
            (ApiCallLog.is_success == True, 1),
            else_=0
        )
        
        query = self.db.query(
            func.date(ApiCallLog.created_at).label('date'),
            func.count(ApiCallLog.log_id).label('call_count'),
            func.sum(ApiCallLog.total_tokens).label('total_tokens'),
            func.avg(success_case).label('success_rate')
        ).filter(
            ApiCallLog.created_at >= start_date,
            ApiCallLog.created_at <= end_date
        )
        
        if user_id:
            query = query.filter(ApiCallLog.user_id == user_id)
        
        if model_id:
            query = query.filter(ApiCallLog.model_id == model_id)
        
        query = query.group_by(
            func.date(ApiCallLog.created_at)
        ).order_by(
            func.date(ApiCallLog.created_at).desc()
        )
        
        results = query.all()
        
        return [
            {
                "date": date.strftime('%Y-%m-%d'),
                "call_count": call_count,
                "total_tokens": total_tokens or 0,
                "success_rate": float(success_rate or 0)
            }
            for date, call_count, total_tokens, success_rate in results
        ]


    
    
    # 修复代码,在现有文件中添加以下两个方法：
    def search_logs(
        self,
        user_id: Optional[int] = None,
        model_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_success: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[ApiCallLog]:
        """
        根据条件搜索API调用日志
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            start_date: 开始日期
            end_date: 结束日期
            is_success: 是否成功
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            API调用日志列表
        """
        from sqlalchemy import and_
        
        query = self.db.query(ApiCallLog).options(
            joinedload(ApiCallLog.user),
            joinedload(ApiCallLog.system_model)
        )
        
        # 构建过滤条件
        filters = []
        if user_id is not None:
            filters.append(ApiCallLog.user_id == user_id)
        if model_id is not None:
            filters.append(ApiCallLog.model_id == model_id)
        if start_date:
            filters.append(ApiCallLog.created_at >= start_date)
        if end_date:
            filters.append(ApiCallLog.created_at <= end_date)
        if is_success is not None:
            filters.append(ApiCallLog.is_success == is_success)
        
        if filters:
            query = query.filter(and_(*filters))
        
        query = query.order_by(desc(ApiCallLog.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def count_logs(
        self,
        user_id: Optional[int] = None,
        model_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_success: Optional[bool] = None
    ) -> int:
        """
        根据条件统计API调用日志数量
        
        Args:
            user_id: 用户ID
            model_id: 模型ID
            start_date: 开始日期
            end_date: 结束日期
            is_success: 是否成功
            
        Returns:
            日志数量
        """
        from sqlalchemy import and_
        
        query = self.db.query(func.count(ApiCallLog.log_id))
        
        # 构建过滤条件
        filters = []
        if user_id is not None:
            filters.append(ApiCallLog.user_id == user_id)
        if model_id is not None:
            filters.append(ApiCallLog.model_id == model_id)
        if start_date:
            filters.append(ApiCallLog.created_at >= start_date)
        if end_date:
            filters.append(ApiCallLog.created_at <= end_date)
        if is_success is not None:
            filters.append(ApiCallLog.is_success == is_success)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.scalar()
    
    def get_user_api_stats(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户API调用统计
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_api_usage_stats(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_overall_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取整体API调用统计
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_api_usage_stats(
            start_date=start_date,
            end_date=end_date
        )