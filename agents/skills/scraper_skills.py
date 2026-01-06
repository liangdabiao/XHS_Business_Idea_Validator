"""
数据抓取 Skills

提供小红书数据抓取的业务技能
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.business_models import XhsNoteModel, XhsCommentModel
from agents.base_agent import BaseAgent


logger = logging.getLogger(__name__)


async def search_posts_skill(
    agent: BaseAgent,
    keyword: str,
    pages: int = 2,
    sort: str = "general",
    note_type: str = "_0"
) -> Dict[str, Any]:
    """
    搜索小红书笔记

    Args:
        agent: Agent 实例
        keyword: 搜索关键词
        pages: 搜索页数
        sort: 排序方式 (general/time/popularity)
        note_type: 笔记类型 (_0全部/_1视频/_2图文)

    Returns:
        搜索结果
    """
    logger.info(f"Searching posts for keyword: {keyword}, pages: {pages}")

    try:
        # 调用 XHS MCP 服务器
        result = await agent.use_mcp(
            server_name="xhs",
            tool_name="search_notes",
            keyword=keyword,
            page=1,
            pages=pages,
            sort=sort,
            note_type=note_type
        )

        if result.get("success"):
            notes = result.get("notes", [])
            logger.info(f"Found {len(notes)} notes for '{keyword}'")

            return {
                "success": True,
                "keyword": keyword,
                "notes": notes,
                "total_count": len(notes),
                "execution_time": result.get("execution_time", 0)
            }
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Search failed: {error}")
            return {
                "success": False,
                "keyword": keyword,
                "notes": [],
                "error": error
            }

    except Exception as e:
        logger.error(f"Search posts skill failed: {e}")
        return {
            "success": False,
            "keyword": keyword,
            "notes": [],
            "error": str(e)
        }


async def get_comments_skill(
    agent: BaseAgent,
    note_id: str,
    limit: int = 50
) -> Dict[str, Any]:
    """
    获取笔记评论

    Args:
        agent: Agent 实例
        note_id: 笔记 ID
        limit: 最大评论数

    Returns:
        评论结果
    """
    logger.info(f"Getting comments for note: {note_id}")

    try:
        # 调用 XHS MCP 服务器
        result = await agent.use_mcp(
            server_name="xhs",
            tool_name="get_note_comments",
            note_id=note_id,
            limit=limit
        )

        if result.get("success"):
            comments = result.get("comments", [])
            logger.info(f"Got {len(comments)} comments for note '{note_id}'")

            return {
                "success": True,
                "note_id": note_id,
                "comments": comments,
                "total_count": len(comments),
                "execution_time": result.get("execution_time", 0)
            }
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Get comments failed: {error}")
            return {
                "success": False,
                "note_id": note_id,
                "comments": [],
                "error": error
            }

    except Exception as e:
        logger.error(f"Get comments skill failed: {e}")
        return {
            "success": False,
            "note_id": note_id,
            "comments": [],
            "error": str(e)
        }


async def batch_get_comments_skill(
    agent: BaseAgent,
    note_ids: List[str],
    comments_per_note: int = 20
) -> Dict[str, Any]:
    """
    批量获取评论

    Args:
        agent: Agent 实例
        note_ids: 笔记 ID 列表
        comments_per_note: 每个笔记的评论数

    Returns:
        批量评论结果
    """
    logger.info(f"Batch getting comments for {len(note_ids)} notes")

    if not note_ids:
        return {
            "success": True,
            "results": {},
            "total_comments": 0,
            "message": "No note IDs provided"
        }

    try:
        # 调用 XHS MCP 服务器
        result = await agent.use_mcp(
            server_name="xhs",
            tool_name="batch_get_comments",
            note_ids=note_ids,
            comments_per_note=comments_per_note
        )

        if result.get("success"):
            results_dict = result.get("results", {})
            total_comments = result.get("total_comments", 0)
            logger.info(f"Batch complete: {total_comments} comments total")

            return {
                "success": True,
                "results": results_dict,
                "total_comments": total_comments,
                "execution_time": result.get("execution_time", 0)
            }
        else:
            error = result.get("error", "Unknown error")
            error_type = result.get("error_type", "")

            # 如果是 CancelledError，保留部分结果
            if error_type == "CancelledError":
                completed = result.get("completed", 0)
                total = result.get("total", len(note_ids))
                results_dict = result.get("results", {})
                total_comments = result.get("total_comments", 0)
                logger.warning(f"Batch partially complete: {completed}/{total} notes, {total_comments} comments")

                return {
                    "success": False,
                    "results": results_dict,
                    "total_comments": total_comments,
                    "error": error,
                    "error_type": error_type,
                    "completed": completed,
                    "total": total
                }
            else:
                logger.error(f"Batch get comments failed: {error}")
                return {
                    "success": False,
                    "results": {},
                    "total_comments": 0,
                    "error": error
                }

    except Exception as e:
        logger.error(f"Batch get comments skill failed: {e}")
        return {
            "success": False,
            "results": {},
            "total_comments": 0,
            "error": str(e)
        }


async def batch_scrape_skill(
    agent: BaseAgent,
    keywords: List[str],
    pages_per_keyword: int = 2,
    comments_per_note: int = 20,
    max_notes: int = 20,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    批量抓取：搜索笔记 + 获取评论

    Args:
        agent: Agent 实例
        keywords: 关键词列表
        pages_per_keyword: 每个关键词的搜索页数
        comments_per_note: 每个笔记的评论数
        max_notes: 最大笔记数
        progress_callback: 进度回调函数

    Returns:
        批量抓取结果
    """
    logger.info(f"Batch scraping for {len(keywords)} keywords")
    # DEBUG: Log all keywords
    logger.debug(f"[SCRAPER] All keywords to process: {keywords}")

    start_time = datetime.now()
    all_notes = []
    all_comments = {}
    keyword_results = {}

    total_keywords = len(keywords)

    for idx, keyword in enumerate(keywords):
        # DEBUG: Log each keyword being processed
        logger.debug(f"[SCRAPER] Processing keyword {idx+1}/{total_keywords}: {keyword}")
        try:
            # 更新进度
            if progress_callback:
                from models.agent_models import ProgressUpdate
                progress = idx / total_keywords  # 0-1 range
                update = ProgressUpdate(
                    step="searching",
                    progress=progress,
                    message=f"正在搜索关键词: {keyword}"
                )
                progress_callback(update)

            # 搜索笔记
            search_result = await search_posts_skill(
                agent,
                keyword=keyword,
                pages=pages_per_keyword
            )

            if not search_result.get("success"):
                logger.warning(f"Search failed for keyword '{keyword}': {search_result.get('error')}")
                keyword_results[keyword] = {
                    "success": False,
                    "notes_count": 0,
                    "comments_count": 0,
                    "error": search_result.get("error")
                }
                continue

            notes = search_result.get("notes", [])
            keyword_notes = notes[:max_notes]
            all_notes.extend(keyword_notes)

            logger.info(f"Found {len(keyword_notes)} notes for '{keyword}'")

            # 获取评论
            comments_result = {"total_comments": 0}  # 初始化默认值
            if keyword_notes and comments_per_note > 0:
                if progress_callback:
                    from models.agent_models import ProgressUpdate
                    progress = (idx + 0.5) / total_keywords  # 0-1 range
                    update = ProgressUpdate(
                        step="fetching_comments",
                        progress=progress,
                        message=f"正在获取 {keyword} 的评论..."
                    )
                    progress_callback(update)

                note_ids = [
                    n.get("note_id") 
                    for n in keyword_notes 
                    if n.get("note_id") and n.get("comments_count", 0) > 0
                ]

                skipped_count = len(keyword_notes) - len(note_ids)
                if skipped_count > 0:
                    logger.info(f"Skipping {skipped_count} notes with comments_count=0 for keyword '{keyword}'")

                if note_ids:
                    comments_result = await batch_get_comments_skill(
                        agent,
                        note_ids=note_ids,
                        comments_per_note=comments_per_note
                    )

                    if comments_result.get("success"):
                        all_comments.update(comments_result.get("results", {}))
                        logger.info(f"Got {comments_result.get('total_comments', 0)} comments for '{keyword}'")

            # 保存关键词结果
            total_comments_for_keyword = sum(
                len(comments) for comments in all_comments.values()
                if any(n.get("note_id") == note_id for n in keyword_notes for note_id in [n.get("note_id")])
            )

            keyword_results[keyword] = {
                "success": True,
                "notes_count": len(keyword_notes),
                "comments_count": comments_result.get("total_comments", 0) if comments_per_note > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to scrape keyword '{keyword}': {e}")
            keyword_results[keyword] = {
                "success": False,
                "notes_count": 0,
                "comments_count": 0,
                "error": str(e)
            }

    execution_time = (datetime.now() - start_time).total_seconds()

    # 最终进度更新
    if progress_callback:
        from models.agent_models import ProgressUpdate
        update = ProgressUpdate(
            step="batch_scrape",
            progress=1.0,  # 100%
            message=f"批量抓取完成: {len(all_notes)} 条笔记, {len(all_comments)} 批次评论"
        )
        progress_callback(update)

    logger.info(f"Batch scrape complete: {len(all_notes)} notes, {len(all_comments)} comment batches in {execution_time:.2f}s")

    return {
        "success": True,
        "notes": all_notes,
        "comments": all_comments,
        "total_notes": len(all_notes),
        "total_comments": sum(len(c) for c in all_comments.values()),
        "keyword_results": keyword_results,
        "execution_time": execution_time
    }


async def batch_scrape_with_comments_skill(
    agent: BaseAgent,
    keywords: List[str],
    pages_per_keyword: int = 2,
    comments_per_note: int = 20,
    max_notes: int = 20,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    批量抓取：搜索笔记 + 获取评论 + 合并在一起

    与 batch_scrape_skill 的区别：
    - 返回 posts_with_comments 结构（每个 post 包含自己的 comments_data）
    - 单一数据结构，更方便后续分析

    Args:
        agent: Agent 实例
        keywords: 关键词列表
        pages_per_keyword: 每个关键词的搜索页数
        comments_per_note: 每个笔记的评论数
        max_notes: 最大笔记数
        progress_callback: 进度回调函数

    Returns:
        批量抓取结果，包含 posts_with_comments
    """
    logger.info(f"Batch scraping with comments for {len(keywords)} keywords")
    # DEBUG: Log keywords
    logger.debug(f"[SCRAPER] Keywords received: {keywords}")

    # 先使用原有的批量抓取逻辑
    scrape_result = await batch_scrape_skill(
        agent,
        keywords=keywords,
        pages_per_keyword=pages_per_keyword,
        comments_per_note=comments_per_note,
        max_notes=max_notes,
        progress_callback=progress_callback
    )

    if not scrape_result.get("success"):
        return {
            "success": False,
            "posts_with_comments": [],
            "metadata": {},
            "error": scrape_result.get("error", "Scraping failed")
        }

    # 获取原始数据
    all_notes = scrape_result.get("notes", [])
    all_comments = scrape_result.get("comments", {})

    # 合并 comments 到 posts
    posts_with_comments = _merge_comments_to_posts(all_notes, all_comments)

    # 计算元数据
    metadata = {
        "total_posts": len(posts_with_comments),
        "posts_with_comments": sum(1 for p in posts_with_comments if p.get("comments_fetched")),
        "posts_without_comments": sum(1 for p in posts_with_comments if not p.get("comments_fetched")),
        "total_comments": sum(len(p.get("comments_data", [])) for p in posts_with_comments),
        "keyword_results": scrape_result.get("keyword_results", {}),
        "execution_time": scrape_result.get("execution_time", 0)
    }

    logger.info(
        f"Batch scrape with comments complete: "
        f"{len(posts_with_comments)} posts, "
        f"{metadata['posts_with_comments']} with comments, "
        f"{metadata['total_comments']} total comments"
    )

    return {
        "success": True,
        "posts_with_comments": posts_with_comments,
        "metadata": metadata
    }


# ============================================================================
# 辅助函数
# ============================================================================

def _merge_comments_to_posts(
    posts: List[Dict[str, Any]],
    comments_dict: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Merge comments into their parent posts

    Args:
        posts: List of posts
        comments_dict: Dictionary {note_id: [comments]}

    Returns:
        List of posts with embedded comments
    """
    posts_with_comments = []

    for post in posts:
        note_id = post.get("note_id")
        post_copy = post.copy()

        # Add comments to post
        comments = comments_dict.get(note_id, [])
        post_copy["comments_data"] = comments
        post_copy["comments_fetched"] = len(comments) > 0
        post_copy["comments_fetch_error"] = None if comments else "No comments fetched"

        posts_with_comments.append(post_copy)

    return posts_with_comments
