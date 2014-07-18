# -*- coding: utf-8 -*-
from openerp.osv import fields,osv
from openerp import tools
from openerp.tools.translate import _
from openerp.modules.registry import RegistryManager
import string

SECURITYLEVEL = [('high','High'),('low','Low'),('middle','Middle')]
EXECUTELEVEL = [('high','High'),('low','Low'),('middle','Middle')]
DATATYPE = [('string','String'),('integer','Integer'),('boolean','Boolean')]
CONTROLTYPE = [('input','Input'),('dropdonlist','DropDownList'),('checkbox','CheckBox'),('radiolist','RadioList')]
RELATIONS = [('hoston',"Host On"),("allocateto","Allocate To"),("parentchild","Parent-Child"),
             ("connected","Connected"),("installedsoftware","Installed Software"),("documentbackup","Document backup"),
             ("dependent","Dependent"),("contains","Contains"),("ispartof","Is part of")]

"""
Positive 正向
Negative 反向
Double   双向
"""
RELATIONTYPES = [("positive","Positive"),("negative","Negative"),("double","Double")]

class RelationType(osv.osv):
    _name = "cmdb.relationtype"
    _columns = {
        "name":fields.char(string="Name",size=100,required=True),
        "code":fields.char(string="Code",size=100,required=True),
        "direction":fields.selection(RELATIONTYPES,string="Direction",size=100,required=True),
        "description":fields.char(string="Description",size=500),
    }
    _sql_constraints = [("code_unique","unique(code)","code must be unique")]

RelationType()

class AssetTemplateCategory(osv.osv):
    _name="cmdb.assettemplatecategory"
    _description = "Asset Template category"

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        print "ids is %s " % ids
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        print res
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    def child_get(self, cr, uid, ids):
        return [ids]

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from cmdb_assettemplatecategory where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True
    
    _columns = {
        'name': fields.char(string='Name', size=64, required=True, translate=True, select=True),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'parent_id': fields.many2one('cmdb.assettemplatecategory',string='Parent', select=True, ondelete='cascade'),
        'child_id': fields.one2many('cmdb.assettemplatecategory', 'parent_id', string='Children'),
        'sequence': fields.integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of product \
                                                             categories."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
        "remark":fields.text(string="Remark")
    }

    _constraints = [
        (_check_recursion, '错误！您不能循环创建目录.', ['parent_id'])
    ]

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = "parent_left"

AssetTemplateCategory()

def get_tree_top2low(objname,cr,uid,parent_id,context=None):
    """
    自顶向下的寻找，不包含自己
    """
    print "objname is %s,cr.dbname is %s,uid is %s,parent_id is %s" % (objname,cr.dbname,uid,parent_id)
    if not objname:
        return None
    registry = RegistryManager.get(cr.dbname)
    rep = registry.get(objname)
    template = rep.read(cr,uid,parent_id,["parent_left","parent_right","id"],context=context)
    if not template:
        return None
    res = rep.search(cr,uid,[("parent_left",">",template["parent_left"]),("parent_right","<",template["parent_right"])],context=context)
    print "get_tree_low2top result is %s" % res
    return res

def get_tree_low2top(tablename,cr,uid,parent_id,context=None):
    """
    从自己向上找，即看自己所在的线上继承了多个元素 
    """    
    print "parent_id is %s" % parent_id
    cr.execute("SELECT A.* FROM %s as A \
                INNER JOIN %s as B \
                ON 1=1 \
                WHERE  A.parent_left < B.parent_left and \
                    A.parent_left < B.parent_right and   \
                    B.parent_left < A.parent_right and   \
                    B.parent_right < A.parent_right      \
                AND b.id=%s                               \
                ORDER BY A.id" % (tablename,tablename, parent_id))
    parent_ids = filter(None,map(lambda x:x[0],cr.fetchall()))
    parent_ids.append(parent_id)
    return parent_ids


def get_list_from_nestedlist(item):
    if not item:
        return []
    res = []
    for line in item:
        for i in line:
            res.append(i)
    return res

class AssetTemplate(osv.osv):
    _name="cmdb.assettemplate"
    _description = "Asset Template"

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        #print "ids is %s " % ids
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        #print res
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    def child_get(self, cr, uid, ids):
        return [ids]

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from cmdb_assettemplate where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True
    
    def get_inherit_attributes(self,cr,uid,ids,name,arg,context=None):
        res = {}
        for template in self.browse(cr,uid,ids,context=context):
            if not template.parent_id:
                continue
            parent_ids = get_tree_low2top("cmdb_assettemplate",cr,uid,template.parent_id.id,context=context) 
            if not parent_ids:
                continue
            attrs = self.read(cr,uid,parent_ids,["id","attributes"],context=context)
            temp = [item["attributes"] for item in attrs]
            attr_ids = get_list_from_nestedlist(temp)
            res[template.id] = attr_ids
        return res

    def get_inherit_actions(self,cr,uid,ids,name,arg,context=None):
        res = {}
        for template in self.browse(cr,uid,ids,context=context):
            if not template.parent_id:
                continue
            parent_ids = get_tree_low2top("cmdb_assettemplate",cr,uid,template.parent_id.id,context=context) 
            if not parent_ids:
                continue
            actions = self.read(cr,uid,parent_ids,["id","actions"],context=context)
            temp = [item["actions"] for item in actions]
            action_ids = get_list_from_nestedlist(temp)
            res[template.id] = action_ids
        return res

    def get_inherit_relations(self,cr,uid,ids,name,arg,context=None):
        res = {}
        for template in self.browse(cr,uid,ids,context=context):
            if not template.parent_id:
                continue
            parent_ids = get_tree_low2top("cmdb_assettemplate",cr,uid,template.parent_id.id,context=context) 
            if not parent_ids:
                continue
            relations = self.read(cr,uid,parent_ids,["id","relations"],context=context)
            temp = [item["relations"] for item in relations]
            relation_ids = get_list_from_nestedlist(temp)
            res[template.id] = relation_ids
        return res

    def onchange_parent_get_inherit_attributes(self,cr,uid,ids,parentid,context=None):
        result = []
        action_res = []
        relation_res = []
        parent_ids =  get_tree_low2top("cmdb_assettemplate",cr,uid,parentid,context=context) 
        #self._get_inherit_tree(cr, uid,parentid, context=context)
        attr_rep = self.pool.get("cmdb.assettemplate.attribute")
        attr_ids = attr_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        for item in attr_rep.read(cr,uid,attr_ids,[],context=context):
            result.append(item)
        
        action_rep = self.pool.get("cmdb.assettemplate.action")
        action_ids = attr_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        for item in action_rep.read(cr,uid,action_ids,[],context=context):
            action_res.append(item)

        relation_rep = self.pool.get("cmdb.assettemplate.relation")
        relation_ids = relation_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        for item in relation_rep.read(cr,uid,action_ids,[],context=context):
            relation_res.append(item)
        #result2[ids] = result
        print "result is %s" % result
        return  {
                    "value": {
                        "inherit_attributes" : result,
                        "inherit_actions": action_res,
                        "inherit_relations": relation_res,
                    }
                }
    
    _columns = {
        "category_id":fields.many2one("cmdb.assettemplatecategory",string="Category",select=True),
        'name': fields.char(string='Name', size=64, required=True, translate=True, select=True),
        "code":fields.char(string="Code",size=200,required=True,help="Code must be unique"),
        "description":fields.char(string="Description",size=1000,required=False,help="Description the target of template"),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'parent_id': fields.many2one('cmdb.assettemplate',string='Parent', select=True, ondelete='cascade'),
        'child_id': fields.one2many('cmdb.assettemplate', 'parent_id', string='Children'),
        "attributes":fields.one2many("cmdb.assettemplate.attribute","assettemplate_id",string="Attributes"),
        "actions":fields.one2many("cmdb.assettemplate.action","assettemplate_id",string="Actions"),
        "relations":fields.one2many("cmdb.assettemplate.relation","assettemplate_id",string="Relations"),
        "inherit_attributes":fields.function(get_inherit_attributes,type="one2many",relation="cmdb.assettemplate.attribute",string="Inherit Attributes"),
        "inherit_actions":fields.function(get_inherit_actions,type="one2many",relation="cmdb.assettemplate.action",string="Inherit Actions"),
        "inherit_relations":fields.function(get_inherit_relations,type="one2many",relation="cmdb.assettemplate.relation",string="Inherit Relations"),
        'sequence': fields.integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of product \
                                                             categories."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
        "remark":fields.text(string="Remark"),
    }

    _constraints = [
        (_check_recursion, '错误！您不能循环创建目录.', ['parent_id'])
    ]

    _defaults = {
        "code":lambda self,cr,uid,context:self.pool.get("ir.sequence").get(cr,uid,"seq.assettemplate.code")
    }


    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = "parent_left"
AssetTemplate()

class AssetTemplateAttribute(osv.osv):
    _name="cmdb.assettemplate.attribute"

    def push_attribute(self,cr,uid,ids,context=None):
        templates = self.read(cr,uid,ids,[],context=context)
        print "templates is %s "%templates 
        if not templates:
            return False
        template = templates[0]
        template_id = template["assettemplate_id"][0]
        res = get_tree_top2low("cmdb.assettemplate",cr,uid,template_id,context=context)
        res.append(template_id)
        #print "push res is %s " % res
        asset_rep = self.pool.get("cmdb.asset")
        asset_ids = asset_rep.search(cr,uid,[("assettemplate_id","in",res)],context=context)
        print "asset_ids is %s " % asset_ids
        asset_attr_rep = self.pool.get("cmdb.asset.attribute")
        for asset_id in asset_ids:
            template["asset_id"] = asset_id
            print "attr instance is %s " % template
            asset_attr_rep.create(cr,uid,template,context=context)
        self.write(cr,uid,ids,{'state':'haspush'},context=context)
        return True
    
    _columns = {
        "assettemplate_id":fields.many2one("cmdb.assettemplate",string="Template"),
        "name":fields.char(string="Name",size=200,required=True,help="The name of the attribute"),
        "code":fields.char(string="Code",size=200,required=True,help="unique"),
        "tooltip":fields.char(string="Tool Tip", size=500),
        "securitylevel":fields.selection(SECURITYLEVEL,string="Security Level"),
        "datatype":fields.selection(DATATYPE, string="Data Type", required=True ),
        "controltype":fields.selection(CONTROLTYPE, string="Control Type",required=True),
        "sourcefrom":fields.char(string="Value Source",size=100,required=True),
        "sourcetype":fields.selection(DATATYPE, string="Source Type",required=False,size=100),
        "defaultvalue":fields.char(string="Default Value",size=500,required=False),
        "remark":fields.char(string="Remark",size=500,required=False),
        "state":fields.selection([("haspush","Pushed"),("nopush","Not Push")],string="State"),
    }

    _defaults = {
        "securitylevel":"low",
        "controltype":"input",
        "sourcetype":"integer",
        "state":"nopush",
        "code":lambda self,cr,uid,context:self.pool.get("ir.sequence").get(cr,uid,"seq.assettemplate.attribute.code")
    }

AssetTemplateAttribute()

class AssetTemplateRelation(osv.osv):
    _name = "cmdb.assettemplate.relation"
    
    _columns = {
        "assettemplate_id":fields.many2one("cmdb.assettemplate",string="AssetTemplate"),
        "relationtype_id":fields.many2one("cmdb.relationtype",string="Relation Type"),
        "assettemplate_id2":fields.many2one("cmdb.assettemplate",string="AssetTemplate To"),
        "relationtype_id2":fields.many2one("cmdb.relationtype",string="Relation from type"),
    }

    _defaults = {
        #"code":lambda self,cr,uid,context:self.pool.get("ir.sequence").get(cr,uid,"seq.assettemplate.relation.code"),
    }
AssetTemplateRelation()

class AssetTemplateAction(osv.osv):
    _name="cmdb.assettemplate.action"
    
    def removeattr(self,cr,uid,ids,context=None):
        self.unlink(cr,uid,ids,context=context)
        #return template_id
        return True

    def push_action(self,cr,uid,ids,context=None):
        templates = self.read(cr,uid,ids,[],context=context)
        print "templates is %s "%templates 
        if not templates:
            return False
        template = templates[0]
        template_id = template["assettemplate_id"][0]
        res = get_tree_top2low("cmdb.assettemplate",cr,uid,template_id,context=context)
        res.append(template_id)
        #print "push res is %s " % res
        asset_rep = self.pool.get("cmdb.asset")
        asset_ids = asset_rep.search(cr,uid,[("assettemplate_id","in",res)],context=context)
        print "asset_ids is %s " % asset_ids
        asset_action_rep = self.pool.get("cmdb.asset.action")
        for asset_id in asset_ids:
            template["asset_id"] = asset_id
            print "action instance is %s " % template
            asset_action_rep.create(cr,uid,template,context=context)
        self.write(cr,uid,ids,{'state':'haspush'},context=context)
        return True
    
    _columns = {
        "assettemplate_id":fields.many2one("cmdb.assettemplate",string="Template"),
        "name":fields.char(string="Name",size=200,required=True,),
        "code":fields.char(string="Code",size=200,required=True,),
        "executelevel":fields.selection(SECURITYLEVEL,string="Execute Level"),
        "estimatetime":fields.integer(string="Estimate Time",required=True,help="Estimate execute time by hour"),
        "command":fields.text(string="Command",required=True,help="Command template,parameters with {name}"),
        "ordernum":fields.integer(string="Order",required=True,help="The execute order"),
        "batch":fields.char(string="Batch",required=False,help="If set batch,must execute together"),
        "state":fields.selection([("haspush","Pushed"),("nopush","Not Push")],string="State"),
    }
    
    _defaults = {
        "executelevel":"low",
        "ordernum":10,
        "state":"nopush",
        "code":lambda self,cr,uid,context:self.pool.get("ir.sequence").get(cr,uid,"seq.assettemplate.action.code")
    }
AssetTemplateAction()

class Asset(osv.osv):
    _name="cmdb.asset"
    _description = "Asset"

    def _get_relation_types(self,cr,uid,ids,context=None):
        pass

    def _get_inherit_tree(self,cr,uid,ids,parent_id,context=None):
        print "parent_id is %s" % parent_id
        cr.execute("SELECT A.* FROM cmdb_assettemplate as A \
                    INNER JOIN cmdb_assettemplate as B \
                    ON 1=1 \
                    WHERE  A.parent_left < B.parent_left and \
                        A.parent_left < B.parent_right and   \
                        B.parent_left < A.parent_right and   \
                        B.parent_right < A.parent_right      \
                    AND b.id=%s                               \
                    ORDER BY A.id" % parent_id)
        parent_ids = filter(None,map(lambda x:x[0],cr.fetchall()))
        parent_ids.append(parent_id)
        return parent_ids

    def onchange_parent_get_inherit_attributes(self,cr,uid,ids,parentid,context=None):
        result = []
        action_result = []
        relation_result = []
        parent_ids =  self._get_inherit_tree(cr, uid, ids, parentid, context=context)
        attr_rep = self.pool.get("cmdb.assettemplate.attribute")
        action_rep = self.pool.get("cmdb.assettemplate.action")
        relation_rep = self.pool.get("cmdb.assettemplate.relation")

        attr_ids = attr_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        action_ids = action_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        relation_ids = relation_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        
        for item in attr_rep.read(cr,uid,attr_ids,[],context=context):
            item["fromtemplate"] ="yes" #item["yes"]
            result.append(item)
            print "attr item is %s " % item
        
        for item in action_rep.read(cr,uid,action_ids,[],context=context):
            action_result.append(item)
        
        for item in relation_rep.read(cr,uid,relation_ids,[],context=context):
            relation_result.append(item)
            print "relationitem is %s " % item 
        #result2[ids] = result
        print "result is %s" % relation_result
        return  {
                    "value": {
                        "attributes" : result,
                        "actions": action_result,
                        "relations": relation_result,
                    }
        }
    
    _columns = {
        #"category_id":fields.many2one("cmdb.assettemplatecategory",string="Category",select=True),
        "name": fields.char(string='Name', size=64, required=True, translate=True, select=True),
        "code":fields.char(string="Code",size=200,required=True,help="Code must be unique"),
        "description":fields.char(string="Description",size=1000,required=False,help="Description the target of template"),
        #"complete_name": fields.function(_name_get_fnc, type="char", string='Full Name'),
        "assettemplate_id": fields.many2one('cmdb.assettemplate',string='Template', select=True, ondelete='cascade'),
        #'child_id': fields.one2many('cmdb.assettemplate', 'parent_id', string='Children'),
        "attributes":fields.one2many("cmdb.asset.attribute","asset_id",string="Attributes"),
        "relations":fields.one2many("cmdb.asset.relation","asset_id",string="Relations"),
        "actions":fields.one2many("cmdb.asset.action","asset_id",string="Actions"),
        #"inherit_attributes":fields.function(get_inherit_attributes,type="one2many",relation="cmdb.assettemplate.attribute",method=True,fnct_search=search_inherit_attributes,string="Inherit Attributes"),
        'sequence': fields.integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of product \
                                                             categories."),
        "remark":fields.text(string="Remark")
    }

    _defaults = {
        "code":lambda self,cr,uid,context:self.pool.get("ir.sequence").get(cr,uid,"seq.asset.code"),
    }

Asset()

class AssetAttribute(osv.osv):
    _name="cmdb.asset.attribute"
   
    def unlink(self,cr,uid,ids,context=None):
        res = self.read(cr,uid,ids,["id","fromtemplate"],context=context)
        print "res %s " % res
        return True

    _columns = {
        "asset_id":fields.many2one("cmdb.asset",string="Asset"),
        "name":fields.char(string="Name",size=200,required=True,help="The name of the attribute"),
        "code":fields.char(string="Code",size=200,required=True,help="unique"),
        "tooltip":fields.char(string="Tool Tip", size=500),
        "securitylevel":fields.selection(SECURITYLEVEL,string="Security Level"),
        "datatype":fields.selection(DATATYPE, string="Data Type", required=False ),
        "controltype":fields.selection(CONTROLTYPE, string="Control Type",required=False),
        "sourcefrom":fields.char(string="Value Source",size=100,required=False),
        "sourcetype":fields.selection(DATATYPE, string="Source Type",required=False,size=100),
        "defaultvalue":fields.char(string="Value",size=500,required=False),
        "fromtemplate":fields.selection([("yes","Yes"),("no","No")],string="FromTemplate"),
        "remark":fields.char(string="Remark",size=500,required=False),
    }

    _defaults = {
        "securitylevel":"low",
        "controltype":"input",
        "sourcetype":"integer",
        "fromtemplate":"no",
    }

AssetAttribute()

class AssetAction(osv.osv):
    _name="cmdb.asset.action"

    def _format_action_command(self,cr,uid,asset_id,command,context=None):
        attr_rep = self.pool.get("cmdb.asset.attribute")
        attr_ids = attr_rep.search(cr,uid,[('asset_id','=',asset_id)],context=context)
        attr_items = attr_rep.read(cr,uid,attr_ids,[],context=context)
        values = {}
        for item in attr_items:
            values[item['code']] = item['defaultvalue']
        t_cmd = string.Template(command)
        content = t_cmd.safe_substitute(values)
        return content

    def get_format_asset_action(self,cr,uid,ids,name,arg,context=None):
        result = dict.fromkeys(ids,'None')
        for item in self.read(cr,uid,ids,['id','asset_id','command'],context=context):
            result[item["id"]] = self._format_action_command(cr,uid,item["asset_id"][0],item["command"],context=context)
            print result
            #result[item["id"]] = "abc"
        return result
    
    _columns = {
        "asset_id":fields.many2one("cmdb.asset",string="Asset"),
        "name":fields.char(string="Name",size=200,required=True,),
        "code":fields.char(string="Code",size=200,required=True,),
        "executelevel":fields.selection(SECURITYLEVEL,string="Execute Level"),
        "estimatetime":fields.integer(string="Estimate Time",required=True,help="Estimate execute time by hour"),
        "command":fields.text(string="Command",required=True,help="Command template,parameters with {name}"),
        "cmdcontent":fields.function(get_format_asset_action,string="CMD Content",type="char"),
        "ordernum":fields.integer(string="Order",required=True,help="The execute order"),
        "batch":fields.char(string="Batch",required=False,help="If set batch,must execute together"),
    }
    
    _defaults = {
        "executelevel":"low",
        "ordernum":10,
    }
AssetAction()

class AssetRelation(osv.osv):
    _name = "cmdb.asset.relation"
   
    def on_change_asset2(self,cr,uid,ids,asset_id,asset_id2,template_relation_id,context=None):
        print "ids is %s, asset_id is %s, asset_id2 is %s " % (ids,asset_id,asset_id2)
        if asset_id2 == asset_id:
            return {
                "value":{
                    "asset_id2":None,
                },
                "warning":{
                    "title":"Warning",
                    "message":"You cannot choose some asset!You must choose another!",
                }
            }
        return {"value":{
                "asset_id2":asset_id2,
            }
        }

    def create(self,cr,uid,data,context=None):
        print "relation is %s " % data
        if data["asset_id"] == data["asset_id2"]:
            raise osv.except_osv(_('Cannot connect to self!'),_("You must select another asset !") )
            
        if isinstance(data["relationtype_id"],(list,tuple)):
            data["relationtype_id"] = data["relationtype_id"][0]
        if isinstance(data["relationtype_id2"],(list,tuple)):
            data["relationtype_id2"] = data["relationtype_id2"][0]
        print "relation is %s " % data
        rel_id = super(AssetRelation,self).create(cr,uid,data,context=context)
        if not rel_id:
            return False
        rel_from = {"asset_id":data["asset_id2"],"relationtype_id":data["relationtype_id2"],"asset_id2":data["asset_id"],"relationtype_id2":data["relationtype_id"]}
        print "rel_from is %s " % rel_from
        super(AssetRelation,self).create(cr,uid,rel_from,context=context)
        return rel_id

    _columns = {
        "asset_id":fields.many2one("cmdb.asset",string="Asset"),
        "template_relation_id":fields.integer(string="Template Relation Id"),
        "relationtype_id":fields.many2one("cmdb.relationtype",string="Asset to type"),
        "asset_id2":fields.many2one("cmdb.asset",string="Asset To"),
        "relationtype_id2":fields.many2one("cmdb.relationtype",string="Relation from type"),
    }

AssetRelation()
