import React from 'react';
import { Form, Row, Col, Input, Button, Select, DatePicker } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface SearchField {
  name: string;
  label: string;
  type: 'input' | 'select' | 'date' | 'dateRange';
  options?: Array<{
    label: string;
    value: string | number;
  }>;
  placeholder?: string;
}

interface SearchFormProps {
  fields: SearchField[];
  onSearch: (values: any) => void;
  onReset?: () => void;
}

const SearchForm: React.FC<SearchFormProps> = ({
  fields,
  onSearch,
  onReset
}) => {
  const [form] = Form.useForm();

  const handleReset = () => {
    form.resetFields();
    onReset?.();
  };

  const renderField = (field: SearchField) => {
    switch (field.type) {
      case 'select':
        return (
          <Select placeholder={field.placeholder}>
            {field.options?.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        );
      case 'date':
        return <DatePicker style={{ width: '100%' }} />;
      case 'dateRange':
        return <RangePicker style={{ width: '100%' }} />;
      default:
        return <Input placeholder={field.placeholder} />;
    }
  };

  return (
    <Form
      form={form}
      className="search-form"
      onFinish={onSearch}
    >
      <Row gutter={16}>
        {fields.map(field => (
          <Col key={field.name} xs={24} sm={12} md={8} lg={6}>
            <Form.Item
              name={field.name}
              label={field.label}
            >
              {renderField(field)}
            </Form.Item>
          </Col>
        ))}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
              搜索
            </Button>
            <Button 
              style={{ marginLeft: 8 }}
              onClick={handleReset}
              icon={<ReloadOutlined />}
            >
              重置
            </Button>
          </Form.Item>
        </Col>
      </Row>
    </Form>
  );
};

export default SearchForm; 