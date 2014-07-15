# -*- coding: utf-8 -*-
from openerp.osv import fields,osv
from openerp import tools
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
        "direction":fields.selection(RELATIONTYPES,size=100,required=True),
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

    def onchange_parent_get_inherit_attributes(self,cr,uid,ids,parentid,context=None):
        result = []
        action_res = []
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
        #result2[ids] = result
        print "result is %s" % result
        return  {
                    "value": {
                        "inherit_attributes" : result,
                        "inherit_actions": action_res,
                    }
                }
        
    def create(self, cr, uid, data, context=None):
        print "create data is %s" % data
        if not data.get("parent_id") or not len(data.get("attributes")):
            pass
        attributes = data.get("attributes")
        needsave_attributes = []
        for row in attributes:
            attr_item = row[2]
            if not attr_item or attr_item.get("assettemplate_id"):
                continue
            print attr_item
            needsave_attributes.append([0,False,attr_item])
        print "needsave_attributes is %s" % needsave_attributes
        data["attributes"] = needsave_attributes
        template_id = super(AssetTemplate, self).create(cr, uid, data, context=context)
        return template_id
    
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
        "inherit_attributes":fields.function(get_inherit_attributes,type="one2many",relation="cmdb.assettemplate.attribute",string="Inherit Attributes"),
        "inherit_actions":fields.function(get_inherit_actions,type="one2many",relation="cmdb.assettemplate.action",string="Inherit Actions"),
        'sequence': fields.integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of product \
                                                             categories."),
        'parent_left': fields.integer('Left parent', select=True),
        'parent_right': fields.integer('Right parent', select=True),
        "remark":fields.text(string="Remark"),
    }

    _constraints = [
        (_check_recursion, '错误！您不能循环创建目录.', ['parent_id'])
    ]


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
    }

AssetTemplateAttribute()

class AssetTemplateAction(osv.osv):
    _name="cmdb.assettemplate.action"
    
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
        parent_ids =  self._get_inherit_tree(cr, uid, ids, parentid, context=context)
        attr_rep = self.pool.get("cmdb.assettemplate.attribute")
        action_rep = self.pool.get("cmdb.assettemplate.action")
        attr_ids = attr_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        action_ids = action_rep.search(cr,uid,[('assettemplate_id','in',parent_ids)],context=context)
        for item in attr_rep.read(cr,uid,attr_ids,[],context=context):
            result.append(item)
        for item in action_rep.read(cr,uid,action_ids,[],context=context):
            action_result.append(item)
        #result2[ids] = result
        print "result is %s" % result
        return  {
                    "value": {
                        "attributes" : result,
                        "actions": action_result
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

Asset()

class AssetAttribute(osv.osv):
    _name="cmdb.asset.attribute"

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
        "remark":fields.char(string="Remark",size=500,required=False),
    }

    _defaults = {
        "securitylevel":"low",
        "controltype":"input",
        "sourcetype":"integer",
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
    
    _columns = {
        "asset_id":fields.many2one("cmdb.asset",string="Asset"),
        "relationtype":fields.selection(RELATIONS,string="Relation",required=True),
        "asset_id2":fields.many2one("cmdb.asset",string="Asset To"),
    }

AssetRelation()
